#!/usr/bin/env bash

set -euo pipefail

DEFAULT_REPO_OWNER="nelsonwellswku"
DEFAULT_REPO_NAME="backlog-boss"
DEFAULT_BRANCH="main"
GITHUB_ISSUER="https://token.actions.githubusercontent.com"
AZURE_AUDIENCE="api://AzureADTokenExchange"

prompt_with_default() {
  local prompt_text="$1"
  local default_value="$2"
  local result=""

  if [ -n "$default_value" ]; then
    read -r -p "${prompt_text} [${default_value}]: " result
    if [ -z "$result" ]; then
      result="$default_value"
    fi
  else
    read -r -p "${prompt_text}: " result
    while [ -z "$result" ]; do
      read -r -p "${prompt_text}: " result
    done
  fi

  printf '%s\n' "$result"
}

confirm_default_yes() {
  local prompt_text="$1"
  local response=""

  read -r -p "${prompt_text} [Y/n]: " response
  case "${response,,}" in
    "" | "y" | "yes")
      return 0
      ;;
    "n" | "no")
      return 1
      ;;
    *)
      echo "Please answer y or n." >&2
      confirm_default_yes "$prompt_text"
      ;;
  esac
}

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
}

slugify() {
  echo "$1" | tr '/_. ' '-' | tr -cd '[:alnum:]-'
}

resolve_app_client_id() {
  local identifier="$1"
  local resolved_app_id=""

  resolved_app_id="$(az ad app show --id "$identifier" --query appId -o tsv 2>/dev/null || true)"
  if [ -n "$resolved_app_id" ]; then
    printf '%s\n' "$resolved_app_id"
    return 0
  fi

  resolved_app_id="$(az ad sp show --id "$identifier" --query appId -o tsv 2>/dev/null || true)"
  if [ -n "$resolved_app_id" ]; then
    printf '%s\n' "$resolved_app_id"
    return 0
  fi

  return 1
}

require_command az

if ! az account show >/dev/null 2>&1; then
  echo "Azure CLI is not logged in yet. Starting az login..."
  az login >/dev/null
fi

current_subscription_id="$(az account show --query id -o tsv)"
current_subscription_name="$(az account show --query name -o tsv)"

echo
echo "Current Azure subscription: ${current_subscription_name} (${current_subscription_id})"
echo

subscription_id="$(prompt_with_default "Azure subscription ID to use" "$current_subscription_id")"
az account set --subscription "$subscription_id"

tenant_id="$(az account show --query tenantId -o tsv)"
subscription_name="$(az account show --query name -o tsv)"

echo
echo "Using Azure subscription: ${subscription_name} (${subscription_id})"
echo "Tenant ID: ${tenant_id}"
echo

app_identifier="$(prompt_with_default "App registration client ID, app object ID, or service principal object ID" "")"
if ! app_client_id="$(resolve_app_client_id "$app_identifier")"; then
  echo "Could not resolve an app registration from '${app_identifier}'." >&2
  exit 1
fi

app_display_name="$(az ad app show --id "$app_client_id" --query displayName -o tsv)"
service_principal_object_id="$(az ad sp show --id "$app_client_id" --query id -o tsv 2>/dev/null || true)"

if [ -z "$service_principal_object_id" ]; then
  echo "No service principal exists for ${app_display_name}. Creating one..."
  az ad sp create --id "$app_client_id" --only-show-errors >/dev/null
  service_principal_object_id="$(az ad sp show --id "$app_client_id" --query id -o tsv)"
fi

echo
echo "Resolved app registration: ${app_display_name}"
echo "Client ID: ${app_client_id}"
echo

repo_owner="$(prompt_with_default "GitHub organization or user" "$DEFAULT_REPO_OWNER")"
repo_name="$(prompt_with_default "GitHub repository name" "$DEFAULT_REPO_NAME")"
branch_name="$(prompt_with_default "GitHub branch that will run the deploy workflow" "$DEFAULT_BRANCH")"

default_credential_name="github-$(slugify "$repo_name")-$(slugify "$branch_name")"
credential_name="$(prompt_with_default "Federated credential name" "$default_credential_name")"
credential_description="GitHub Actions OIDC for ${repo_owner}/${repo_name} on branch ${branch_name}"
subject="repo:${repo_owner}/${repo_name}:ref:refs/heads/${branch_name}"

credential_payload=$(cat <<EOF
{
  "name": "${credential_name}",
  "issuer": "${GITHUB_ISSUER}",
  "subject": "${subject}",
  "description": "${credential_description}",
  "audiences": [
    "${AZURE_AUDIENCE}"
  ]
}
EOF
)

if az ad app federated-credential show --id "$app_client_id" --federated-credential-id "$credential_name" >/dev/null 2>&1; then
  az ad app federated-credential update \
    --id "$app_client_id" \
    --federated-credential-id "$credential_name" \
    --parameters "$credential_payload" \
    --only-show-errors \
    >/dev/null
  credential_action="Updated"
else
  az ad app federated-credential create \
    --id "$app_client_id" \
    --parameters "$credential_payload" \
    --only-show-errors \
    >/dev/null
  credential_action="Created"
fi

resource_group_name=""
webapp_name=""

echo
echo "${credential_action} federated credential '${credential_name}' with subject:"
echo "  ${subject}"
echo

if confirm_default_yes "Assign an Azure RBAC role to this service principal for the App Service deploy workflow?"; then
  echo
  echo "Role assignment scope:"
  echo "  1) Specific App Service web app (recommended)"
  echo "  2) Entire resource group"
  role_scope_choice="$(prompt_with_default "Choose scope" "1")"

  case "$role_scope_choice" in
    "1")
      resource_group_name="$(prompt_with_default "Azure resource group name" "")"
      webapp_name="$(prompt_with_default "Azure App Service web app name" "")"
      role_name="$(prompt_with_default "Azure role name" "Website Contributor")"
      role_scope="$(az webapp show --resource-group "$resource_group_name" --name "$webapp_name" --query id -o tsv)"
      ;;
    "2")
      resource_group_name="$(prompt_with_default "Azure resource group name" "")"
      role_name="$(prompt_with_default "Azure role name" "Contributor")"
      role_scope="$(az group show --name "$resource_group_name" --query id -o tsv)"
      ;;
    *)
      echo "Unsupported scope choice: ${role_scope_choice}" >&2
      exit 1
      ;;
  esac

  existing_role_count="$(az role assignment list \
    --assignee-object-id "$service_principal_object_id" \
    --scope "$role_scope" \
    --query "[?roleDefinitionName=='${role_name}'] | length(@)" \
    -o tsv)"

  if [ "$existing_role_count" = "0" ]; then
    az role assignment create \
      --assignee-object-id "$service_principal_object_id" \
      --assignee-principal-type ServicePrincipal \
      --role "$role_name" \
      --scope "$role_scope" \
      --only-show-errors \
      >/dev/null
    echo
    echo "Assigned Azure role '${role_name}'."
  else
    echo
    echo "Azure role '${role_name}' is already assigned at the selected scope."
  fi
fi

echo
echo "GitHub repository secrets to set:"
echo "  AZURE_CLIENT_ID=${app_client_id}"
echo "  AZURE_TENANT_ID=${tenant_id}"
echo "  AZURE_SUBSCRIPTION_ID=${subscription_id}"

if [ -n "$resource_group_name" ]; then
  echo
  echo "GitHub repository variables to set:"
  echo "  AZURE_RESOURCE_GROUP=${resource_group_name}"
  if [ -n "$webapp_name" ]; then
    echo "  AZURE_WEBAPP_NAME=${webapp_name}"
  fi
fi

echo
echo "This repo no longer uses GitHub Environments for Azure deploy auth."
echo "The federated credential trusts branch-based OIDC tokens from:"
echo "  ${subject}"

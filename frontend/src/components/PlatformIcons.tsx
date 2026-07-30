import Box from "@mui/material/Box";
import Tooltip from "@mui/material/Tooltip";
import { FaWindows, FaApple, FaLinux } from "react-icons/fa";
import type { IconType } from "react-icons";

const PLATFORM_ORDER = [6, 14, 3];

const PLATFORMS: Record<number, { name: string; color: string; icon: IconType }> = {
  6: { name: "Windows", color: "#00A4EF", icon: FaWindows },
  14: { name: "Mac", color: "#555555", icon: FaApple },
  3: { name: "Linux", color: "#B8860B", icon: FaLinux },
};

export function PlatformIcon({ platformId }: { platformId: number }) {
  const platform = PLATFORMS[platformId];
  if (!platform) return null;

  const Icon = platform.icon;

  return (
    <Tooltip title={platform.name}>
      <Box
        component="span"
        sx={{
          display: "inline-flex",
          alignItems: "center",
          lineHeight: 0,
          color: platform.color,
        }}
      >
        <Icon size={20} />
      </Box>
    </Tooltip>
  );
}

export function PlatformIcons({ platformIds }: { platformIds: number[] | undefined }) {
  if (!platformIds || platformIds.length === 0) return null;

  return (
    <Box
      component="span"
      sx={{
        display: "inline-flex",
        alignItems: "center",
        gap: 0.25,
        ml: 0.5,
      }}
    >
      {[...platformIds].sort((a, b) => PLATFORM_ORDER.indexOf(a) - PLATFORM_ORDER.indexOf(b)).map((id) => (
        <PlatformIcon key={id} platformId={id} />
      ))}
    </Box>
  );
}

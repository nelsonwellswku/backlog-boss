import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
  Stack,
} from "@mui/material";
import {
  VideogameAsset,
  TrendingUp,
  Schedule,
  Star,
  EmojiEvents,
} from "@mui/icons-material";
import { useCurrentUser } from "@bb/hooks/useCurrentUser";
import { Link } from "react-router";

export function Home() {
  const { isSuccess, data } = useCurrentUser();
  const isLoggedIn = isSuccess && data?.data;

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
          py: 8,
          borderRadius: 2,
          mb: 6,
          textAlign: "center",
        }}
      >
        <Container maxWidth="md">
          <EmojiEvents sx={{ fontSize: 80, mb: 2 }} />
          <Typography variant="h2" component="h1" gutterBottom fontWeight="bold">
            Conquer Your Gaming Backlog
          </Typography>
          <Typography variant="h5" sx={{ mb: 4, opacity: 0.95 }}>
            Stop wondering what to play next. Let Backlog Boss prioritize your
            game library so you can focus on playing.
          </Typography>
          {!isLoggedIn ? (
            <Typography variant="h6" sx={{ opacity: 0.9 }}>
              Sign in with Steam to get started
            </Typography>
          ) : (
            <Button
              component={Link}
              to="/my-backlog"
              variant="contained"
              size="large"
              sx={{
                bgcolor: "white",
                color: "#667eea",
                fontSize: "1.1rem",
                px: 4,
                py: 1.5,
                "&:hover": {
                  bgcolor: "#f0f0f0",
                },
              }}
            >
              View My Backlog
            </Button>
          )}
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ mb: 6 }}>
        <Typography
          variant="h3"
          component="h2"
          textAlign="center"
          gutterBottom
          sx={{ mb: 5 }}
        >
          Why Backlog Boss?
        </Typography>

        <Grid container spacing={4}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Card
              sx={{
                height: "100%",
                textAlign: "center",
                transition: "transform 0.2s",
                "&:hover": { transform: "translateY(-8px)" },
              }}
            >
              <CardContent sx={{ py: 4 }}>
                <VideogameAsset
                  sx={{ fontSize: 60, color: "#667eea", mb: 2 }}
                />
                <Typography variant="h5" component="h3" gutterBottom>
                  Smart Organization
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Automatically sync your Steam library and organize your games
                  with intelligent categorization and filtering.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card
              sx={{
                height: "100%",
                textAlign: "center",
                transition: "transform 0.2s",
                "&:hover": { transform: "translateY(-8px)" },
              }}
            >
              <CardContent sx={{ py: 4 }}>
                <TrendingUp sx={{ fontSize: 60, color: "#764ba2", mb: 2 }} />
                <Typography variant="h5" component="h3" gutterBottom>
                  Priority Ranking
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Get personalized recommendations based on ratings, playtime,
                  and your gaming preferences.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card
              sx={{
                height: "100%",
                textAlign: "center",
                transition: "transform 0.2s",
                "&:hover": { transform: "translateY(-8px)" },
              }}
            >
              <CardContent sx={{ py: 4 }}>
                <Schedule sx={{ fontSize: 60, color: "#667eea", mb: 2 }} />
                <Typography variant="h5" component="h3" gutterBottom>
                  Track Progress
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Monitor your gaming journey and see your progress as you work
                  through your backlog.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* How It Works Section */}
      <Box sx={{ bgcolor: "#f5f5f5", py: 6, borderRadius: 2, mb: 6 }}>
        <Container maxWidth="md">
          <Typography
            variant="h3"
            component="h2"
            textAlign="center"
            gutterBottom
            sx={{ mb: 4 }}
          >
            How It Works
          </Typography>

          <Stack spacing={3}>
            <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
              <Box
                sx={{
                  bgcolor: "#667eea",
                  color: "white",
                  borderRadius: "50%",
                  width: 40,
                  height: 40,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: "bold",
                  flexShrink: 0,
                }}
              >
                1
              </Box>
              <Box>
                <Typography variant="h6" gutterBottom>
                  Connect Your Steam Account
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Securely sign in with Steam to automatically import your game
                  library.
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
              <Box
                sx={{
                  bgcolor: "#764ba2",
                  color: "white",
                  borderRadius: "50%",
                  width: 40,
                  height: 40,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: "bold",
                  flexShrink: 0,
                }}
              >
                2
              </Box>
              <Box>
                <Typography variant="h6" gutterBottom>
                  Let Us Prioritize
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Our algorithm analyzes your games and suggests what to play
                  based on multiple factors.
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
              <Box
                sx={{
                  bgcolor: "#667eea",
                  color: "white",
                  borderRadius: "50%",
                  width: 40,
                  height: 40,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: "bold",
                  flexShrink: 0,
                }}
              >
                3
              </Box>
              <Box>
                <Typography variant="h6" gutterBottom>
                  Start Playing!
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Pick from your prioritized list and actually finish those
                  games you've been meaning to play.
                </Typography>
              </Box>
            </Box>
          </Stack>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box sx={{ textAlign: "center", py: 6 }}>
        <Star sx={{ fontSize: 60, color: "#ffd700", mb: 2 }} />
        <Typography variant="h4" gutterBottom>
          Ready to Take Control?
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {isLoggedIn
            ? "Your gaming library awaits!"
            : "Sign in with Steam and start conquering your backlog today."}
        </Typography>
        {isLoggedIn && (
          <Button
            component={Link}
            to="/my-backlog"
            variant="contained"
            size="large"
            sx={{
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              fontSize: "1.1rem",
              px: 4,
              py: 1.5,
            }}
          >
            Go to My Backlog
          </Button>
        )}
      </Box>
    </Box>
  );
}

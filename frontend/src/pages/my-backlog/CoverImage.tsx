import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const IGDB_CDN_BASE = "https://images.igdb.com/igdb/image/upload/t_cover_big";

function coverImageUrl(imageId: string): string {
  return `${IGDB_CDN_BASE}/${imageId}.jpg`;
}

function CoverPlaceholder({ title }: { title: string }) {
  return (
    <Box
      sx={{
        width: 88,
        height: 124,
        borderRadius: 1,
        backgroundColor: "grey.200",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <Typography variant="h5" color="text.secondary">
        {title.charAt(0).toUpperCase()}
      </Typography>
    </Box>
  );
}

type CoverImageProps = {
  imageId?: string | null;
  title: string;
};

export function CoverImage({ imageId, title }: CoverImageProps) {
  if (imageId) {
    return (
      <Box
        component="img"
        src={coverImageUrl(imageId)}
        alt={title}
        loading="lazy"
        sx={{
          width: 88,
          height: 124,
          objectFit: "cover",
          borderRadius: 1,
          flexShrink: 0,
        }}
      />
    );
  }
  return <CoverPlaceholder title={title} />;
}

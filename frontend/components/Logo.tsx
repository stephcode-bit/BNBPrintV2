export default function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect width="48" height="48" rx="12" fill="#0B0E11" />
      <rect width="48" height="48" rx="12" stroke="#F0B90B" strokeOpacity="0.25" />
      {/* central diamond */}
      <path d="M24 14L30 20L24 26L18 20L24 14Z" fill="#F0B90B" />
      {/* four orbiting shards, evoking a mint/print burst */}
      <path d="M12 20L15.5 23.5L12 27L8.5 23.5L12 20Z" fill="#F0B90B" />
      <path d="M36 20L39.5 23.5L36 27L32.5 23.5L36 20Z" fill="#F0B90B" />
      <path d="M24 30L27.5 33.5L24 37L20.5 33.5L24 30Z" fill="#F0B90B" />
      <path d="M24 30L27.5 33.5L24 37L20.5 33.5L24 30Z" fill="#F0B90B" fillOpacity="0" />
      <path d="M24 8L27.5 11.5L24 15L20.5 11.5L24 8Z" fill="#F0B90B" fillOpacity="0.55" />
    </svg>
  );
}

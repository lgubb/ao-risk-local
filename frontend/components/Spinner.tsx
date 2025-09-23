export default function Spinner({ size = 16 }: { size?: number }) {
  const style: React.CSSProperties = {
    width: size,
    height: size,
    border: '2px solid rgba(255,255,255,0.25)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    display: 'inline-block',
    animation: 'spin 0.8s linear infinite',
    verticalAlign: 'middle',
  };
  return <span style={style} />;
}


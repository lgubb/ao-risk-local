import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AO Risk',
  description: 'Frontend for AO Risk',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>
        <div className="container">
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}

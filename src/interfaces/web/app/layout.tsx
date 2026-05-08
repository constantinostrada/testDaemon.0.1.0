import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mini-Library",
  description: "Manage your personal book collection with Mini-Library API.",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps): JSX.Element {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="container">
            <h1 className="site-title">📚 Mini-Library</h1>
            <nav className="site-nav">
              <a href="/">My Books</a>
              <a href="/catalog">Catalog</a>
              <a href="/add">Add Book</a>
            </nav>
          </div>
        </header>
        <main className="site-main">
          <div className="container">{children}</div>
        </main>
        <footer className="site-footer">
          <div className="container">
            <p>Mini-Library API — Built with FastAPI &amp; Next.js</p>
          </div>
        </footer>
      </body>
    </html>
  );
}

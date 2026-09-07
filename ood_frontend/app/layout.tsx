import type { Metadata } from "next";
import { IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const ibmPlexSans = IBM_Plex_Sans({
  variable: "--font-ibm-plex-sans",
  subsets: ["latin"],
  weight: ["300", "400", "600"],
});

export const metadata: Metadata = {
  title: "University Enrollment",
  description: "Register for university course sections.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return <html lang="en" className={ibmPlexSans.variable}><body>{children}</body></html>;
}

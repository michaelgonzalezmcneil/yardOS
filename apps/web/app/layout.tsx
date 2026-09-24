import type { Metadata } from "next";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

export const metadata: Metadata = { metadataBase:new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"), title:"YardOS — Intelligence for the Physical World", description:"YardOS turns autonomous aerial systems into persistent intelligence for industrial sites.", openGraph:{title:"YardOS — Intelligence for the Physical World",description:"YardOS turns autonomous aerial systems into persistent intelligence for industrial sites.",type:"website",images:[{url:"/og.png",width:1733,height:907,alt:"YardOS — Intelligence for the physical world."}]},twitter:{card:"summary_large_image",title:"YardOS — Intelligence for the Physical World",description:"YardOS turns autonomous aerial systems into persistent intelligence for industrial sites.",images:["/og.png"]} };
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}

import { redirect } from "next/navigation";

// The middleware decides auth; landing on "/" simply forwards into the app.
export default function Home() {
  redirect("/queue");
}

import { redirect } from "next/navigation";

export default function Home() {
  // Redirect to Practice tab by default
  redirect("/practice");
}

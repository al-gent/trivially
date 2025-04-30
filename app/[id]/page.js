"use client";
import Home from "../page";
import { useParams } from "next/navigation";

export default function SharedQuiz() {
  const params = useParams();
  return <Home sharedId={params.id} />;
}
// "use client";
// import { useEffect } from "react";
// import { useRouter } from "next/navigation";
// import Home from "../page";

// export default function SharedQuiz({ params }) {
//   const router = useRouter();
//   const { id } = params;

//   useEffect(() => {
//     // Store the ID in sessionStorage so the Home component can use it
//     if (id) {
//       sessionStorage.setItem("sharedQuestionId", id);
//     }
//   }, [id]);

//   // Reuse the Home component
//   return <Home />;
// }

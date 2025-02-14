import { NextResponse } from "next/server";
import { Pool } from "@neondatabase/serverless"; 
// or import { Pool } from "pg"; if you're using the pg library

// Create a connection pool.
// Make sure NEON_DATABASE_URL is set in your environment variables.
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export async function GET() {
  const client = await pool.connect();

  try {
    // Adjust the table name to match your schema/table
    const query = `
      SELECT id, q, ca, ica1, ica2, ica3, category, difficulty, rating, subject
      FROM questions
      ORDER BY id DESC
      LIMIT 10;
    `;
    const { rows } = await client.query(query);

    // Transform each row into a consistent shape for the client
    const questions = rows.map((row) => ({
      id: row.id,
      question_text: row.q,
      correct_answer: row.ca,
      // Build an array of possible answers
      // (Optionally, you can shuffle them to avoid revealing which is correct)
      answers: [row.ca, row.ica1, row.ica2, row.ica3],
      category: row.category,
      difficulty: row.difficulty,
      rating: row.rating,
      subject: row.subject,
    }));

    return NextResponse.json(questions);
  } catch (error) {
    console.error("Error fetching questions:", error);
    return NextResponse.json({ error: "Failed to retrieve questions" }, { status: 500 });
  } finally {
    client.release();
  }
}

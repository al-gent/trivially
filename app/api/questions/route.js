import { NextResponse } from "next/server";
import { Pool } from "@neondatabase/serverless";

// or import { Pool } from "pg"; if you're using the pg library

// Create a connection pool.
// Make sure NEON_DATABASE_URL is set in your environment variables.
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export async function GET(request) {
  const client = await pool.connect();

  try {
    // Get latest question ID if it is from a shared link
    const url = new URL(request.url);
    const shared = url.searchParams.get("id");
    let query;
    let rows;
    if (shared) {
      query = `
      SELECT id, q, ca, ica1, ica2, ica3, category, difficulty, rating, subject
      FROM questions
      WHERE id <= $1
      ORDER BY id DESC
      LIMIT 10;
    `;
      const result = await client.query(query, [shared]);
      rows = result.rows;
    } else {
      query = `
      SELECT id, q, ca, ica1, ica2, ica3, category, difficulty, rating, subject
      FROM questions
      ORDER BY id DESC
      LIMIT 10;
    `;
      const result = await client.query(query);
      rows = result.rows;
    }

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

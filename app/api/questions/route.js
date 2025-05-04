import { NextResponse } from "next/server";
import { Pool } from "@neondatabase/serverless";

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
      SELECT id, q, ca, ica1, ica2, ica3
      FROM questions
      WHERE id <= $1
      ORDER BY id DESC
      LIMIT 10;
    `;
      const result = await client.query(query, [shared]);
      rows = result.rows;
    } else {
      query = `
      SELECT id, q, ca, ica1, ica2, ica3
      FROM questions
      ORDER BY id DESC
      LIMIT 10;
    `;
      const result = await client.query(query);
      rows = result.rows;
    }

    // In your GET route, modify the mapping:
    const questions = rows.map((row) => ({
      id: row.id,
      question_text: row.q,
      correct_answer: row.ca,
      // Include both the answer text and its original identifier
      answers: [
        { text: row.ca, type: 'ca' },
        { text: row.ica1, type: 'ica1' },
        { text: row.ica2, type: 'ica2' },
        { text: row.ica3, type: 'ica3' }
      ],
    }));

    return NextResponse.json(questions);
  } catch (error) {
    console.error("Error fetching questions:", error);
    return NextResponse.json({ error: "Failed to retrieve questions" }, { status: 500 });
  } finally {
    client.release();
  }
}

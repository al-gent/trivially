import { NextResponse } from "next/server";
import { Pool } from "@neondatabase/serverless";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export async function POST(request, { params }) {
  const client = await pool.connect();
  
  try {
    const questionId = params.id;
    console.log(questionId)
    // Update the upvotes count
    const query = `
      UPDATE questions 
      SET downvotes = downvotes + 1 
      WHERE id = $1
      RETURNING downvotes;
    `;
    
    const result = await client.query(query, [questionId]);
    
    if (result.rowCount === 0) {
      return NextResponse.json(
        { error: 'Question not found' },
        { status: 404 }
      );
    }
    
    // Return the new upvote count
    return NextResponse.json({ 
      success: true,
      upvotes: result.rows[0].upvotes 
    });
    
  } catch (error) {
    console.error('Error upvoting question:', error);
    return NextResponse.json(
      { error: 'Failed to upvote question' },
      { status: 500 }
    );
  } finally {
    client.release();
  }
}
import { NextResponse } from "next/server";
import { Pool } from "@neondatabase/serverless";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export async function POST(request, { params }) {
  const client = await pool.connect();
  
  try {
    // Get the question ID from params
    const { id: questionId } = await params;
        
    // Parse the request body to get the answer data
    const body = await request.json();
    const { answer_text, answer_type } = body;
    
    console.log('Question ID:', questionId);
    console.log('Selected Answer:', answer_text);
    console.log('type:', answer_type);
    
    const columnMap = {
        'ca': 'ca_sel',
        'ica1': 'ica1_sel',
        'ica2': 'ica2_sel',
        'ica3': 'ica3_sel'
      };
      
      const columnToUpdate = columnMap[answer_type];
      
      if (!columnToUpdate) {
        return NextResponse.json({ error: 'Invalid answer type' }, { status: 400 });
      }
      
      const query = `
        UPDATE questions 
        SET ${columnToUpdate} = ${columnToUpdate} + 1
        WHERE id = $1
        RETURNING id, ${columnToUpdate};
      `;
    const result = await client.query(query, [
      questionId,

    ]);
    
    return NextResponse.json({
      success: true,
      selectionId: result.rows[0].id
    });
    
  } catch (error) {
    console.error('Error logging answer selection:', error);
    return NextResponse.json(
      { error: 'Failed to log answer selection' },
      { status: 500 }
    );
  } finally {
    client.release();
  }
}
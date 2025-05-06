"use client";
import { useEffect, useState } from "react";
import Image from "next/image";

export default function Home({ sharedId }) {
  const [questions, setQuestions] = useState([]);
  const [answerStatus, setAnswerStatus] = useState({});
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [questionFeedback, setQuestionFeedback] = useState({});

  function shuffleArray(array) {
    return array.slice().sort(() => Math.random() - 0.5);
  }

  useEffect(() => {
    const url = sharedId
      ? `/api/questions?id=${sharedId}`
      : "/api/questions";
      
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        console.log("Received data:", data);
        const questionsWithShuffledAnswers = data.map((q) => ({
          ...q,
          answers: shuffleArray(q.answers), // This now shuffles objects, not just strings
        }));
        setQuestions(questionsWithShuffledAnswers);
      })
      .catch((error) => console.error("Error fetching questions:", error));
  }, [sharedId]);

  const handleAnswerClick = async (questionId, answer, correctAnswer) => {
    const isCorrect = answer.text === correctAnswer;
    if (answerStatus[questionId]) {
      return;
    }

    // Highlight the chosen answer
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: answer.text
    }));
    

    // Set correct/incorrect feedback
    setAnswerStatus((prev) => ({
      ...prev,
      [questionId]: isCorrect ? "correct" : "incorrect",
    }));


    try {
      console.log(answer)
      await fetch(`/api/questions/${questionId}/selection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          answer_text: answer.text,
          answer_type: answer.type
        }),
      });
    } catch (error) {
      console.error('Error logging answer:', error);
    }

  };

  const handleFeedback = async (questionId, feedback) => {
    setQuestionFeedback(prev => ({
      ...prev,
      [questionId]: feedback
    }));
    const slug = `${feedback}vote`;
    try {
    const response = await fetch(`/api/questions/${questionId}/${slug}`, {
      method: 'POST',
    });
    
    if (!response.ok) throw new Error('Failed to upvote');
    
    const data = await response.json();
    console.log('Upvote successful:', data);
    
    // Update local state or refetch data
    // For example: setUpvotes(prev => prev + 1)
    
  } catch (error) {
    console.error('Error upvoting:', error);
  }
};

  // Function that handles the share button click event
  const handleShareClick = () => {
    const percentage = (correctAnswers / totalQuestions) * 100;
    // Get the id of the first question
    const questionId = questions[0]?.id;
    let shareScore;
    if (percentage === 100) {
      shareScore =  `🏆 Try Beating My Score! ${percentage}% - Doubt you can! 😳`;
    } else if (percentage >= 70) {
      shareScore =  `🫡 Giving you a shot today! ${percentage}% - Let's see what you got! 📚`;
    } else {
      shareScore =  `😢 Didn't do too hot. ${percentage}% - Don't lose! 🤷🏽‍♂️`;
    }
    shareScore = `${shareScore}\nPlay at https://trivially-gamma.vercel.app/${questionId}`;
    // Copy the generated share URL to the user's clipboard
    navigator.clipboard.writeText(shareScore);
    // Show a confirmation message to the user that the link was copied
    alert("Share score copied to clipboard!");
  };

  const totalQuestions = questions.length;
  const correctAnswers = Object.values(answerStatus).filter(
    (status) => status === "correct"
  ).length;
  const allAnswered =
    totalQuestions > 0 && Object.keys(answerStatus).length === totalQuestions;

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 sm:p-20 font-sans">
      <main className="flex flex-col items-center gap-8 row-start-2 w-full max-w-2xl mx-auto">
        {questions.length === 0 ? (
          <Image
            src="/trivialy_logo.gif"
            alt="Trivialy logo"
            width={400}
            height={38}
            unoptimized
            priority
          />
        ) : (
          <Image
            src="/trivially.webp"
            alt="Trivialy logo"
            width={400}
            height={38}
            unoptimized
            priority
          />
        )}
        <h2 className="text-xl font-semibold">Today's Questions</h2>

        {/* Question List */}
        <div className="flex flex-col gap-8 w-full">
          {questions.length === 0 ? (
            <p>Loading questions...</p>
          ) : (
            questions.map((q) => {
              const currentQuestionStatus = answerStatus[q.id];

              return (
                <div
                  key={q.id}
                  className="p-4 border rounded-md shadow-sm bg-white dark:bg-gray-800 relative"
                >
                  {/* Question Text */}
                  <p className="mb-2 font-medium text-lg">{q.question_text}</p>

        {/* Multiple-Choice Answers */}
        <ul className="flex flex-col gap-2">
          {q.answers.map((answer, idx) => {
            const isSelected = selectedAnswers[q.id] === answer.text;
            return (
              <li key={idx}>
                <button
                  className={`rounded-md border px-3 py-1
                    hover:bg-gray-100 dark:hover:bg-gray-700
                    text-black dark:text-white
                    ${isSelected && currentQuestionStatus === "correct" && "bg-green-600"}
                    ${isSelected && currentQuestionStatus === "incorrect" && "bg-red-600"}
                    ${answer.text === q.correct_answer && currentQuestionStatus === "incorrect" && "bg-green-600"}
                  `}
                  disabled={!!currentQuestionStatus}
                  onClick={() => {
                    console.log(answer.text, answer.type);
                    handleAnswerClick(q.id, answer, q.correct_answer);
                  }}
                >
                  {answer.text}
                </button>
              </li>
            );
          })}
        </ul>

                  {/* Correct/Incorrect Feedback */}
                  {currentQuestionStatus && (
                    <div className="mt-2">
                      {currentQuestionStatus === "correct" ? (
                        <span className="text-green-600">Correct!</span>
                      ) : (
                        <span className="text-red-600">Incorrect</span>
                      )}
                    </div>
                  )}

                  {/* Feedback Buttons */}
                  <div className="flex justify-end gap-2 mt-4">
                    <button
                      onClick={() => handleFeedback(q.id, 'up')}
                      className={`p-2 rounded-full transition-colors ${
                        questionFeedback[q.id] === 'up' 
                          ? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300' 
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500'
                      }`}
                    >
                      👍
                    </button>
                    <button
                      onClick={() => handleFeedback(q.id, 'down')}
                      className={`p-2 rounded-full transition-colors ${
                        questionFeedback[q.id] === 'down' 
                          ? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300' 
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500'
                      }`}
                    >
                      👎
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Score Display */}
        {allAnswered && (
          <div className="flex justify-center items-center gap-4">
            <div className="mt-6 p-4 border rounded-md shadow-md bg-green-100 dark:bg-green-800">
              <h3 className="text-lg font-semibold">Quiz Complete!</h3>
              <p className="text-md">
                Your score: {correctAnswers} / {totalQuestions}
              </p>
            </div>
            <button 
              onClick={handleShareClick}
              className="mt-6 p-4 border rounded-md shadow-md bg-blue-100 dark:bg-blue-800 hover:bg-blue-200 dark:hover:bg-blue-700 transition-colors cursor-pointer"
            >
              <h3 className="text-lg font-semibold">Flex on your friends!</h3>
            </button>
          </div>
        )}
      </main>

      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center">
        <p className="text-sm text-gray-500">© YOLO_SWAG_AI</p>
      </footer>
    </div>
  );
}

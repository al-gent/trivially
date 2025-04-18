"use client";
import { useEffect, useState } from "react";
import Image from "next/image";

export default function Home() {
  const [questions, setQuestions] = useState([]);
  const [answerStatus, setAnswerStatus] = useState({});
  const [selectedAnswers, setSelectedAnswers] = useState({});

  // Utility function to shuffle array
  function shuffleArray(array) {
    return array.slice().sort(() => Math.random() - 0.5);
  }

  useEffect(() => {
    fetch("/api/questions")
      .then((res) => res.json())
      .then((data) => {
        // Shuffle the answers for each question
        const questionsWithShuffledAnswers = data.map((q) => ({
          ...q,
          answers: shuffleArray(q.answers),
        }));
        setQuestions(questionsWithShuffledAnswers);
      })
      .catch((error) => console.error("Error fetching questions:", error));
  }, []);

  const handleAnswerClick = (questionId, chosenAnswer, correctAnswer) => {
    // If the user has already answered this question, do nothing
    if (answerStatus[questionId]) {
      return;
    }

    // Highlight the chosen answer
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: chosenAnswer,
    }));

    // Set correct/incorrect feedback
    setAnswerStatus((prev) => ({
      ...prev,
      [questionId]: chosenAnswer === correctAnswer ? "correct" : "incorrect",
    }));
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
        {/* Example Logo/Image (optional) */}
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
                  className="p-4 border rounded-md shadow-sm bg-white dark:bg-gray-800"
                >
                  {/* Question Text */}
                  <p className="mb-2 font-medium text-lg">{q.question_text}</p>

                  {/* Multiple-Choice Answers */}
                  <ul className="flex flex-col gap-2">
                    {q.answers.map((answer, idx) => {
                      const isSelected = selectedAnswers[q.id] === answer;

                      return (
                        <li key={idx}>
                          <button
                            className={`rounded-md border px-3 py-1
                              hover:bg-gray-100 dark:hover:bg-gray-700
                              text-black dark:text-white
                              ${isSelected && currentQuestionStatus === "correct" && "bg-green-600"}
                              ${isSelected && currentQuestionStatus === "incorrect" && "bg-red-600"}
                              ${answer === q.correct_answer && currentQuestionStatus === "incorrect" && "bg-green-600"}
                            `}
                            disabled={!!currentQuestionStatus}
                            onClick={() =>
                              handleAnswerClick(q.id, answer, q.correct_answer)
                            }
                          >
                            {answer}
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
                </div>
              );
            })
          )}
        </div>

        {/* Score Display */}
        {allAnswered && (
          <div className="mt-6 p-4 border rounded-md shadow-md bg-green-100 dark:bg-green-800">
            <h3 className="text-lg font-semibold">Quiz Complete!</h3>
            <p className="text-md">
              Your score: {correctAnswers} / {totalQuestions}
            </p>
          </div>
        )}
      </main>

      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center">
        <p className="text-sm text-gray-500">© YOLO_SWAG_AI</p>
      </footer>
    </div>
  );
}

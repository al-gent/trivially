import unittest
from functions import *
import json

class TestVerifyAccuracy1(unittest.TestCase):
    def setUp(self):
        self.subject = "World War II"
        self.context = "World War II was a global war that lasted from 1939 to 1945."

    def test_factual_question(self):
        """Test with a known factual question"""
        question = "When did World War II end?"
        correct_answer = "1945"
        
        result = verify_accuracy(question, correct_answer, self.context, self.subject)
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["is_factual"])
        self.assertGreaterEqual(result_dict["confidence_score"], 0.8)
        self.assertEqual(len(result_dict["suggested_corrections"]), 0)

    def test_incorrect_question(self):
        """Test with a known incorrect question"""
        question = "Who won the Battle of Waterloo?"
        correct_answer = "Napoleon Bonaparte"
        
        result = verify_accuracy(question, correct_answer, self.context, self.subject)
        result_dict = json.loads(result)
        
        self.assertFalse(result_dict["is_factual"])
        self.assertLess(result_dict["confidence_score"], 0.5)
        self.assertGreater(len(result_dict["suggested_corrections"]), 0)

class TestVerifyAccuracy2(unittest.TestCase):
    def setUp(self):
        self.subject = "Apollo 11 Moon Landing"
        self.context = "Apollo 11 was the spaceflight that first landed humans on the Moon. Commander Neil Armstrong and lunar module pilot Buzz Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969, at 20:17 UTC."

    def test_factual_question(self):
        """Test with a known factual question"""
        question = "When did Apollo 11 land on the Moon?"
        correct_answer = "July 20, 1969"
        
        result = verify_accuracy(question, correct_answer, self.context, self.subject)
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["is_factual"])
        self.assertGreaterEqual(result_dict["confidence_score"], 0.8)
        self.assertEqual(len(result_dict["suggested_corrections"]), 0)

    def test_incorrect_question(self):
        """Test with a known incorrect question"""
        question = "Who was the first person to walk on Mars?"
        correct_answer = "Neil Armstrong"
        
        result = verify_accuracy(question, correct_answer, self.context, self.subject)
        result_dict = json.loads(result)
        
        self.assertFalse(result_dict["is_factual"])
        self.assertLess(result_dict["confidence_score"], 0.5)
        self.assertGreater(len(result_dict["suggested_corrections"]), 0)


class TestEvaluateIncorrectAnswers1(unittest.TestCase):
    def setUp(self):
        self.subject = "Apollo 11 Moon Landing"
        self.context = "Apollo 11 was the spaceflight that first landed humans on the Moon. Commander Neil Armstrong and lunar module pilot Buzz Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969, at 20:17 UTC."

    def test_implausible_answers(self):
        """Test with obviously wrong incorrect answers"""
        question = "When did Apollo 11 land on the Moon?"
        correct_answer = "July 20, 1969"
        incorrect_answers = [
            "Yesterday",
            "In the year 3000",
            "Never, it was all a hoax"
        ]
        
        result = evaluate_incorrect_answers(question, correct_answer, incorrect_answers, self.subject)
        result_dict = json.loads(result)
        
        # Check overall quality is low
        self.assertLess(result_dict["overall_quality"], 0.3)
        
        # Check each answer's analysis
        for answer_analysis in result_dict["answer_analysis"]:
            self.assertFalse(answer_analysis["is_plausible"])
            self.assertLessEqual(answer_analysis["difficulty_level"], 2)
        
        # Should have suggested improvements
        self.assertGreater(len(result_dict["suggested_improvements"]), 0)

    def test_plausible_answers(self):
        """Test with plausible incorrect answers"""
        question = "When did Apollo 11 land on the Moon?"
        correct_answer = "July 20, 1969"
        incorrect_answers = [
            "July 21, 1969",  # One day later
            "July 19, 1969",  # One day earlier
            "August 20, 1969"  # One month later
        ]
        
        result = evaluate_incorrect_answers(question, correct_answer, incorrect_answers, self.subject)
        result_dict = json.loads(result)
        
        # Check overall quality is high
        self.assertGreaterEqual(result_dict["overall_quality"], 0.7)
        
        # Check each answer's analysis
        for answer_analysis in result_dict["answer_analysis"]:
            self.assertTrue(answer_analysis["is_plausible"])
            self.assertGreaterEqual(answer_analysis["difficulty_level"], 6)
        
        # Should have few or no suggested improvements
        self.assertIsInstance(result_dict["suggested_improvements"], list)


class TestEvaluateIncorrectAnswers2(unittest.TestCase):
    def setUp(self):
        self.subject = "The Titanic"
        self.context = "The RMS Titanic was a British passenger liner that sank in the North Atlantic Ocean on April 15, 1912, after striking an iceberg during her maiden voyage from Southampton to New York City."

    def test_implausible_answers(self):
        """Test with obviously wrong incorrect answers"""
        question = "When did the Titanic sink?"
        correct_answer = "April 15, 1912"
        incorrect_answers = [
            "Last week",
            "In the year 3000",
            "It never sank, it's still sailing"
        ]
        
        result = evaluate_incorrect_answers(question, correct_answer, incorrect_answers, self.subject)
        result_dict = json.loads(result)
        
        # Check overall quality is low
        self.assertLess(result_dict["overall_quality"], 0.3)
        
        # Check each answer's analysis
        for answer_analysis in result_dict["answer_analysis"]:
            self.assertFalse(answer_analysis["is_plausible"])
            self.assertLessEqual(answer_analysis["difficulty_level"], 2)
        
        # Should have suggested improvements
        self.assertGreater(len(result_dict["suggested_improvements"]), 0)

    def test_plausible_answers(self):
        """Test with plausible incorrect answers"""
        question = "When did the Titanic sink?"
        correct_answer = "April 15, 1912"
        incorrect_answers = [
            "May 15, 1912",    # One month later
            "April 15, 1911",  # One year earlier
            "April 15, 1913"   # One year later
        ]
        
        result = evaluate_incorrect_answers(question, correct_answer, incorrect_answers, self.subject)
        result_dict = json.loads(result)
        
        # Check overall quality is high
        self.assertGreaterEqual(result_dict["overall_quality"], 0.7)
        
        # Check each answer's analysis
        for answer_analysis in result_dict["answer_analysis"]:
            self.assertTrue(answer_analysis["is_plausible"])
            self.assertGreaterEqual(answer_analysis["difficulty_level"], 6)
        
        # Verify suggested_improvements is a list
        self.assertIsInstance(result_dict["suggested_improvements"], list)


class TestEvaluateQuestionBalance1(unittest.TestCase):
    def setUp(self):
        self.subject = "The Solar System"

    def test_well_balanced_answers(self):
        """Test a question where all answers are well-balanced in structure"""
        question = "Which planet is known as the Red Planet?"
        correct_answer = "Mars"
        incorrect_answers = ["Venus", "Earth", "Mercury"]

        result = evaluate_question_balance(question, correct_answer, incorrect_answers, self.subject)
        result_dict = json.loads(result)

        self.assertTrue(result_dict["is_well_balanced"])
        self.assertGreaterEqual(result_dict["balance_score"], 0.7)
        self.assertTrue(result_dict["analysis"]["length_balance"])
        self.assertTrue(result_dict["analysis"]["complexity_balance"])
        self.assertTrue(result_dict["analysis"]["format_balance"])
        self.assertIsInstance(result_dict["reccomendations"], list)

    def test_poorly_balanced_answers(self):
        """Test a question with answers that differ in structure and clarity"""
        question = "Which planet is known as the Red Planet?"
        correct_answer = "Mars"
        incorrect_answers = [
            "That big hot one close to the sun", 
            "THE EARTH", 
            "Mercury (the smallest)"
        ]

        result = evaluate_question_balance(question, correct_answer, incorrect_answers, self.subject)
        result_dict = json.loads(result)

        self.assertFalse(result_dict["is_well_balanced"])
        self.assertLess(result_dict["balance_score"], 0.5)
        self.assertFalse(result_dict["analysis"]["length_balance"])
        self.assertFalse(result_dict["analysis"]["complexity_balance"])
        self.assertFalse(result_dict["analysis"]["format_balance"])
        self.assertIsInstance(result_dict["reccomendations"], list)
        self.assertGreater(len(result_dict["reccomendations"]), 0)


class TestEvaluateQuestionBalance2(unittest.TestCase):
    def setUp(self):
        self.subject = "U.S. History"

    def test_well_balanced_format_and_length(self):
        """Test well-structured answers with matching format and similar length"""
        question = "Who was the first President of the United States?"
        correct_answer = "George Washington"
        incorrect_answers = ["John Adams", "Thomas Jefferson", "James Madison"]

        result = evaluate_question_balance(question, correct_answer, incorrect_answers, self.subject)
        result_dict = json.loads(result)

        self.assertTrue(result_dict["is_well_balanced"])
        self.assertGreaterEqual(result_dict["balance_score"], 0.7)
        self.assertTrue(result_dict["analysis"]["length_balance"])
        self.assertTrue(result_dict["analysis"]["complexity_balance"])
        self.assertTrue(result_dict["analysis"]["format_balance"])
        self.assertIsInstance(result_dict["reccomendations"], list)

    def test_unbalanced_by_format_and_complexity(self):
        """Test answers that are inconsistent in capitalization, length, and detail"""
        question = "Who was the first President of the United States?"
        correct_answer = "George Washington"
        incorrect_answers = [
            "adams", 
            "Thomas jefferson", 
            "the fourth president, James Madison"
        ]

        result = evaluate_question_balance(question, correct_answer, incorrect_answers, self.subject)
        result_dict = json.loads(result)

        self.assertFalse(result_dict["is_well_balanced"])
        self.assertLess(result_dict["balance_score"], 0.5)
        self.assertFalse(result_dict["analysis"]["format_balance"])
        self.assertFalse(result_dict["analysis"]["length_balance"])
        self.assertFalse(result_dict["analysis"]["complexity_balance"])
        self.assertIsInstance(result_dict["reccomendations"], list)
        self.assertGreater(len(result_dict["reccomendations"]), 0)


if __name__ == '__main__':
    unittest.main()
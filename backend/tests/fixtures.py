"""
Sample test data for integration tests
"""

# Sample ChatGPT conversation export
SAMPLE_CHATGPT_CONVERSATION = {
    "id": "test_conversation_1",
    "title": "AI and Philosophy Discussion",
    "create_time": 1234567890.0,
    "update_time": 1234567900.0,
    "mapping": {
        "message_1": {
            "id": "message_1",
            "message": {
                "id": "message_1",
                "author": {"role": "user"},
                "create_time": 1234567890.0,
                "content": {
                    "content_type": "text",
                    "parts": ["What is consciousness?"]
                }
            },
            "parent": None,
            "children": ["message_2"]
        },
        "message_2": {
            "id": "message_2",
            "message": {
                "id": "message_2",
                "author": {"role": "assistant"},
                "create_time": 1234567895.0,
                "content": {
                    "content_type": "text",
                    "parts": ["Consciousness is one of the most fascinating and debated topics in philosophy and neuroscience..."]
                }
            },
            "parent": "message_1",
            "children": ["message_3"]
        },
        "message_3": {
            "id": "message_3",
            "message": {
                "id": "message_3",
                "author": {"role": "user"},
                "create_time": 1234567900.0,
                "content": {
                    "content_type": "text",
                    "parts": ["Can AI ever be truly conscious?"]
                }
            },
            "parent": "message_2",
            "children": []
        }
    }
}

# Sample manual transcript
SAMPLE_MANUAL_TRANSCRIPT = """
User: I've been thinking about my career path lately.
Assistant: That's an important topic to reflect on. What's been on your mind?
User: I love coding, but I'm not sure if I want to stay in pure engineering forever.
Assistant: Many engineers feel this way. What aspects of your current work do you enjoy most?
User: I like solving problems and building things, but I also want to have more impact on strategy and direction.
Assistant: It sounds like you might be interested in roles that combine technical expertise with leadership, like a technical lead or engineering manager position.
"""

# Sample Gemini JSON export
SAMPLE_GEMINI_JSON = {
    "conversations": [
        {
            "id": "gemini_conv_1",
            "title": "Machine Learning Discussion",
            "created_time": "2024-01-01T00:00:00Z",
            "turns": [
                {
                    "role": "user",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "content": "Explain neural networks to me"
                },
                {
                    "role": "model",
                    "timestamp": "2024-01-01T00:00:05Z",
                    "content": "Neural networks are computing systems inspired by biological neural networks..."
                }
            ]
        }
    ]
}

# Sample persona profile
SAMPLE_PERSONA = {
    "name": "Alice Johnson",
    "core_values": [
        "intellectual growth",
        "authenticity",
        "helping others",
        "work-life balance"
    ],
    "goals": [
        "Become an expert in AI/ML",
        "Build products that help people learn",
        "Achieve financial independence",
        "Maintain healthy relationships"
    ],
    "fears": [
        "Becoming irrelevant in fast-changing tech",
        "Losing passion for work",
        "Missing out on personal life",
        "Not making meaningful impact"
    ],
    "traits": {
        "openness": 90,
        "conscientiousness": 75,
        "extraversion": 55,
        "agreeableness": 80,
        "neuroticism": 45
    },
    "motivations": [
        "Mastery and competence",
        "Autonomy in decision-making",
        "Connection with like-minded people",
        "Contributing to something bigger"
    ],
    "conflicts": [
        "Ambition vs work-life balance",
        "Need for stability vs desire for innovation",
        "Perfectionism vs pragmatism"
    ],
    "psychological_notes": {
        "maslow_level": "Self-actualization",
        "primary_need": "Growth and autonomy",
        "attachment_style": "Secure",
        "cognitive_style": "Analytical with creative bursts"
    }
}

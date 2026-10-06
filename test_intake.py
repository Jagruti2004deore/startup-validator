from app.db import init_db, create_run
from app.state import initial_state
from app.agents.intake import intake_node

init_db()
ideas = [
    "A study-buddy app that matches college students in India into small groups "
    "for exam preparation, with a shared study planner and weekly mock quizzes.",
    "An app for farmers.",
]
for idea in ideas:
    state = initial_state(create_run(idea), idea)
    print(intake_node(state)["profile"], "\n")
import gradio as gr

from query import ask


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", ""

    result = ask(question)

    answer = result["answer"]
    sources = "\n".join(
        f"• {source}"
        for source in result["sources"]
    )

    return answer, sources


with gr.Blocks(title="PS5 Game Discovery Guide") as demo:
    gr.Markdown("# PS5 Game Discovery Guide")
    gr.Markdown(
        "Ask a question about PS5 game recommendations. "
        "Answers are grounded only in the retrieved project documents."
    )

    question = gr.Textbox(
        label="Your question",
        placeholder="Example: What is a good co-op shooter to play on PS5?",
    )

    ask_button = gr.Button("Ask")

    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=5)

    ask_button.click(
        handle_query,
        inputs=question,
        outputs=[answer, sources],
    )

    question.submit(
        handle_query,
        inputs=question,
        outputs=[answer, sources],
    )


demo.launch()
def loop(events, inputs, self):

    if "get" in events or inputs.get("link"):
        load(inputs["link"])
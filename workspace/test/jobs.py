from argparse import ArgumentParser


def hello_world(name=None):
    if name:
        return f"Hello {name}!"
    return "Hello World!"


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--name", default=None)

    args = parser.parse_args()
    print(hello_world(args.name))

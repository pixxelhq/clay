import os

import jinja2

"""
def create_image(source_dir: str, tag: str, build_args: dict) -> Tuple:
    client = docker.from_env()
    img_tag, build_log_iter = client.images.build(
        path=source_dir, tag=tag, buildargs=build_args
    )
    print(f"Docker Image {img_tag} successfully created on local machine")
    return img_tag, build_log_iter
"""


def create_dockerfile(source_dir: str, docker_opts: dict) -> str:
    # all runs `custom run commands` will be run after all the template runs
    # are completed

    environment = jinja2.Environment(loader=jinja2.FileSystemLoader("ramen/templates/"))
    template = environment.get_template("Dockerfile-template.jinja")
    content = template.render(docker_opts)

    with open(os.path.join(source_dir, "Dockerfile"), "w+") as f:
        f.write(content)

    return content


"""
def push_image_to_acr() -> None:
    raise NotImplementedError
"""

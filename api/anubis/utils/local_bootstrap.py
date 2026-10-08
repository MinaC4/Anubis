from anubis.constants import ANUBIS_IMAGE_REGISTRY
from anubis.models import TheiaImage, TheiaImageTag, db
from anubis.utils.data import with_context


@with_context
def bootstrap_personal_instance():
    images = (
        ("theia-base", "Python IDE", "devicon-python-plain", True),
        ("theia-admin", "Admin IDE", "devicon-python-plain", False),
    )
    for repository, title, icon, public in images:
        image_name = f"{ANUBIS_IMAGE_REGISTRY}/{repository}"
        image = TheiaImage.query.filter_by(image=image_name).first()
        if image is None:
            image = TheiaImage(
                image=image_name,
                title=title,
                description=title,
                icon=icon,
                default_tag="python-3.12",
                public=public,
            )
            db.session.add(image)
            db.session.flush()

        tag = TheiaImageTag.query.filter_by(image_id=image.id, tag="python-3.12").first()
        if tag is None:
            db.session.add(TheiaImageTag(
                image_id=image.id,
                tag="python-3.12",
                title="Python 3.12",
                description=title,
            ))
    db.session.commit()


if __name__ == "__main__":
    bootstrap_personal_instance()

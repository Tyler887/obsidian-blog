import os.path
from lib import blog, config, fs
from lib.logger import log
from lib.models.BuilderContext import BuilderContext
from lib.models.Image import Image
from lib.models.Page import Page
from lib.models.Post import Post


_global_context = BuilderContext(
    config = {
      "ASSETS_PATH": "/" + config.ASSETS_DEST_DIR,
      "BLOG_TITLE": config.BLOG_TITLE,
    },
    layouts = {},
    pages = [],
    posts = []
)


def build():
  _prepare_context()
  _make_build_dir()
  _copy_assets_to_build_dir()

  for page in _global_context.get("pages"): _build_page(page)
  for post in _global_context.get("posts"): _build_post(post)


def _prepare_context():
  """Parse layouts, pages, and posts"""
  _global_context["layouts"] = blog.get_layouts()
  _global_context["posts"] = blog.get_posts()
  _global_context["pages"] = blog.get_pages()


def _make_build_dir():
  """Purge old build artefacts and make an empty destination dir"""
  fs.rm_dir(config.DEST_DIR)
  log("Remove build dir")
  fs.make_dir(config.DEST_DIR)
  log("Create a new build dir")

def _copy_assets_to_build_dir():
  fs.copy_dir(config.ASSETS_DIR, os.path.join(config.DEST_DIR, config.ASSETS_DEST_DIR))
  log("Copy assets to the build dir")


def _build_page(page: Page):
  template = page.get("template")
  context = dict(_global_context) | dict(page=page)
  html = template(context)

  slug = page.get("slug")
  dest = os.path.join(config.DEST_DIR, slug)

  layout_name = page.get("layout") or config.DEFAULT_LAYOUT
  layout = _global_context.get("layouts").get(layout_name)
  if layout is not None:
    html = layout.get("template")(context | { "content": html })

  log("Build a page:", page.get("meta").get("title"))
  with open(dest, 'a') as f: print(html, file=f)


def _build_post(post: Post):
  slug = post.get("slug")
  dest = os.path.join(config.DEST_DIR, slug)
  html = post.get("html", "")
  context = dict(_global_context) | dict(post=post)

  layout_name = post.get("layout") or "main"
  layout = _global_context.get("layouts").get(layout_name)
  if layout is not None:
    html = layout.get("template")(context | { "content": html })

  log("Build a post:", post.get("meta").get("title"))
  os.makedirs(os.path.dirname(dest), exist_ok=True)
  with open(dest, 'a') as f: print(html, file=f)

  _copy_images(post.get("imgs", []))


def _copy_images(imgs: list[Image]):
  for img in imgs:
    slug = img.get("slug")
    src = img.get("file")
    dest = os.path.join(config.DEST_DIR, config.ASSETS_DEST_DIR, slug)
    log("  Copy image", src)
    fs.copy_file(src, dest)


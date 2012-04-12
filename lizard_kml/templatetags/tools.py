from django.template import Library
from django.template.defaulttags import URLNode, url


register = Library()


class AbsoluteURLNode(URLNode):
    def render(self, context):
        path = super(AbsoluteURLNode, self).render(context)
        return context['view'].request.build_absolute_uri(path)


@register.tag
def absurl(parser, token, node_cls=AbsoluteURLNode):
    """Just like {% url %}, but return the absolute URL."""

    node_instance = url(parser, token)
    return node_cls(
        view_name=node_instance.view_name,
        args=node_instance.args,
        kwargs=node_instance.kwargs,
        asvar=node_instance.asvar
    )

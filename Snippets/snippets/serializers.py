from django.contrib.auth import get_user_model
from pygments.lexers import get_all_lexers
from pygments.styles import get_all_styles
from rest_framework import serializers

from .models import Snippet

LANGUAGES = sorted((aliases[0], name) for name, aliases, _, _ in get_all_lexers() if aliases)
STYLES = sorted(get_all_styles())


class SnippetSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    highlight = serializers.HyperlinkedIdentityField(view_name="snippet-highlight", format="html")
    code = serializers.CharField(trim_whitespace=False, style={"base_template": "textarea.html"})
    language = serializers.ChoiceField(choices=LANGUAGES, default="python")
    style = serializers.ChoiceField(choices=STYLES, default="friendly")

    class Meta:
        model = Snippet
        fields = ("url", "id", "highlight", "owner", "title", "code", "linenos", "language", "style")


class UserSerializer(serializers.HyperlinkedModelSerializer):
    snippets = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name="snippet-detail")

    class Meta:
        model = get_user_model()
        fields = ("url", "id", "username", "snippets")

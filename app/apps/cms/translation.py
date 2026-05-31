from modeltranslation.translator import register, TranslationOptions
from .models import Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        'site_name', 'site_tagline', 'hero_badge', 'hero_title',
        'hero_subtitle', 'about_text', 'footer_text',
        'meta_title', 'meta_description', 'meta_keywords',
    )


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
    required_languages = ('ru',)


@register(Project)
class ProjectTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'project_type', 'technologies')
    required_languages = ('ru',)


@register(Partner)
class PartnerTranslationOptions(TranslationOptions):
    fields = ('name', 'industry')
    required_languages = ('ru',)


@register(TechStack)
class TechStackTranslationOptions(TranslationOptions):
    fields = ('name', 'label')


@register(WhyUs)
class WhyUsTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
    required_languages = ('ru',)


@register(Stat)
class StatTranslationOptions(TranslationOptions):
    fields = ('value_text', 'label', 'suffix', 'description')

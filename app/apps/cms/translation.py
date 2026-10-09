from modeltranslation.translator import register, TranslationOptions
from .models import (
    Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings,
    CooperationFormat, ProcessStep, Commitment, TeamMember, ProjectImage,
)


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        'site_name', 'site_tagline', 'hero_badge', 'hero_title',
        'hero_subtitle', 'about_text', 'about_photo_caption', 'footer_text',
        'meta_title', 'meta_description', 'meta_keywords',
    )


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
    required_languages = ('ru',)


@register(Project)
class ProjectTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'project_type', 'technologies',
              'task', 'solution', 'result')
    required_languages = ('ru',)


@register(Partner)
class PartnerTranslationOptions(TranslationOptions):
    fields = ('name', 'industry', 'about')
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


@register(CooperationFormat)
class CooperationFormatTranslationOptions(TranslationOptions):
    fields = ('title', 'audience', 'description', 'terms', 'cta_label')
    required_languages = ('ru',)


@register(ProcessStep)
class ProcessStepTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
    required_languages = ('ru',)


@register(Commitment)
class CommitmentTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
    required_languages = ('ru',)


@register(TeamMember)
class TeamMemberTranslationOptions(TranslationOptions):
    fields = ('name', 'role')
    required_languages = ('ru',)


@register(ProjectImage)
class ProjectImageTranslationOptions(TranslationOptions):
    fields = ('caption',)

import json
import re
import typing

from .. import types


# Maximum allowed length for a regex pattern from user-supplied rulesets
_MAX_PATTERN_LENGTH = 2048


def _safe_compile(pattern, flags=0):
    """Compile a regex pattern with basic safety checks against ReDoS."""
    if len(pattern) > _MAX_PATTERN_LENGTH:
        raise re.error(f"Pattern exceeds maximum allowed length of {_MAX_PATTERN_LENGTH}")
    return re.compile(pattern, flags)


def rulesets_from_files(iterable_of_paths: typing.Iterable, ignored_providers: typing.Optional[typing.Iterable] = None) -> types.Rulesets:

    iterable_of_dicts = []

    for ruleset in iterable_of_paths:
        with open(file=ruleset, mode="r") as file:
            content = file.read()

        iterable_of_dicts.append(json.loads(content))

    rulesets = types.Rulesets()

    for ruleset in iterable_of_dicts:

        for providerName in ruleset["providers"].keys():

            if ignored_providers is not None and providerName in ignored_providers:
                continue

            # https://docs.clearurls.xyz/latest/specs/rules/#urlpattern
            urlPattern = types.Pattern(ruleset["providers"][providerName]["urlPattern"])
            urlPattern.compiled = re.compile(urlPattern)

            # https://docs.clearurls.xyz/latest/specs/rules/#completeprovider
            completeProvider = ruleset["providers"][providerName].get("completeProvider", False)

            # https://docs.clearurls.xyz/latest/specs/rules/#rules
            rules = types.Patterns()

            for rule in ruleset["providers"][providerName].get("rules", []):
                pattern = types.Pattern(rule)
                pattern.compiled = re.compile(rf"(%(?:26|23)|&|^){rule}(?:(?:=|%3[Dd])[^&]*)")

                rules.append(pattern)

            # https://docs.clearurls.xyz/latest/specs/rules/#rawrules
            rawRules = types.Patterns()

            for rawRule in ruleset["providers"][providerName].get("rawRules", []):
                pattern = types.Pattern(rawRule)
                pattern.compiled = re.compile(rawRule)

                rawRules.append(pattern)

            # https://docs.clearurls.xyz/latest/specs/rules/#referralmarketing
            referralMarketing = types.Patterns()

            for referral in ruleset["providers"][providerName].get("referralMarketing", []):
                pattern = types.Pattern(referral)
                pattern.compiled = re.compile(rf"(%(?:26|23)|&|^){referral}(?:(?:=|%3[Dd])[^&]*)")

                referralMarketing.append(pattern)

            # https://docs.clearurls.xyz/latest/specs/rules/#exceptions
            exceptions = types.Patterns()

            for exception in ruleset["providers"][providerName].get("exceptions", []):
                pattern = types.Pattern(exception)
                pattern.compiled = re.compile(exception)

                exceptions.append(pattern)

            # https://docs.clearurls.xyz/latest/specs/rules/#redirections
            redirections = types.Patterns()

            for redirection in ruleset["providers"][providerName].get("redirections", []):
                pattern = types.Pattern(redirection)
                pattern.compiled = re.compile(f"{redirection}.*")

                redirections.append(pattern)

            # https://docs.clearurls.xyz/latest/specs/rules/#forceredirection
            # This field is ignored by Unalix, we are leaving it here just as reference
            forceRedirection = ruleset["providers"][providerName].get("forceRedirection", False)

            rulesets.add_ruleset(
                types.Ruleset(
                    providerName=providerName,
                    urlPattern=urlPattern,
                    completeProvider=completeProvider,
                    rules=rules,
                    rawRules=rawRules,
                    referralMarketing=referralMarketing,
                    exceptions=exceptions,
                    redirections=redirections,
                    forceRedirection=forceRedirection
                )
            )

    return rulesets


def rulesets_from_dict(ruleset_dict: dict, ignored_providers: typing.Optional[typing.Iterable] = None) -> types.Rulesets:

    rulesets = types.Rulesets()

    for providerName in ruleset_dict["providers"].keys():

        if ignored_providers is not None and providerName in ignored_providers:
            continue

        provider = ruleset_dict["providers"][providerName]

        urlPattern = types.Pattern(provider["urlPattern"])
        urlPattern.compiled = _safe_compile(urlPattern)

        completeProvider = provider.get("completeProvider", False)

        rules = types.Patterns()
        for rule in provider.get("rules", []):
            pattern = types.Pattern(rule)
            pattern.compiled = _safe_compile(rf"(%(?:26|23)|&|^){rule}(?:(?:=|%3[Dd])[^&]*)")
            rules.append(pattern)

        rawRules = types.Patterns()
        for rawRule in provider.get("rawRules", []):
            pattern = types.Pattern(rawRule)
            pattern.compiled = _safe_compile(rawRule)
            rawRules.append(pattern)

        referralMarketing = types.Patterns()
        for referral in provider.get("referralMarketing", []):
            pattern = types.Pattern(referral)
            pattern.compiled = _safe_compile(rf"(%(?:26|23)|&|^){referral}(?:(?:=|%3[Dd])[^&]*)")
            referralMarketing.append(pattern)

        exceptions = types.Patterns()
        for exception in provider.get("exceptions", []):
            pattern = types.Pattern(exception)
            pattern.compiled = _safe_compile(exception)
            exceptions.append(pattern)

        redirections = types.Patterns()
        for redirection in provider.get("redirections", []):
            pattern = types.Pattern(redirection)
            pattern.compiled = _safe_compile(f"{redirection}.*")
            redirections.append(pattern)

        forceRedirection = provider.get("forceRedirection", False)

        rulesets.add_ruleset(
            types.Ruleset(
                providerName=providerName,
                urlPattern=urlPattern,
                completeProvider=completeProvider,
                rules=rules,
                rawRules=rawRules,
                referralMarketing=referralMarketing,
                exceptions=exceptions,
                redirections=redirections,
                forceRedirection=forceRedirection
            )
        )

    return rulesets

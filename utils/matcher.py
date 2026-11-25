def find_teammates(user_skills, profiles, limit=4):
    """Rank profiles by complementary and shared skills."""
    user_set = {skill.lower() for skill in user_skills}
    ranked = []

    for profile in profiles:
        profile_skills = {skill.lower() for skill in profile["skills"]}
        overlap = user_set & profile_skills
        complement = profile_skills - user_set

        score = len(overlap) + (2 * len(complement))
        rank = {
            **profile,
            "score": score,
            "match_reason": (
                f"Adds {', '.join(sorted(complement)) or 'similar strengths'} "
                f"and shares {len(overlap)} skill(s)."
            ),
        }
        ranked.append(rank)

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]

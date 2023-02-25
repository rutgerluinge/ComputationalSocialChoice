from STVComputations import Profile, remove_alternative, print_profiles


def test_alternative_removal():
    profiles = []

    profiles.append(Profile([1, 2, 3, 4], 1))
    profiles.append(Profile([2, 1, 3, 4], 1))
    profiles.append(Profile([1, 2, 1, 4], 1))
    profiles.append(Profile([1, 2, 3, 4], 1))
    profiles.append(Profile([4, 1, 2, 3], 1))
    profiles.append(Profile([4, 2, 3, 1], 1))

    profiles_2 = remove_alternative(profiles, [1])

    print_profiles(profiles_2)
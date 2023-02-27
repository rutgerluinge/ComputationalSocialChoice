from dataclasses import dataclass
import re


@dataclass
class Profile:
    """class to contain every row of data """
    ballot: list[int]
    count: int

def format_ballot2(ballot:str)-> str:
    ballot = ballot.strip()
    equal = re.findall(r'{.*?}', ballot)
    if equal:
        sub = re.sub(r',','=', equal[0][1:-1])
        ballot = re.sub(r'{.*?}', sub, ballot)

    order = re.sub(r',', '>', ballot)
    print(order)

    return ""

def format_ballot(ballot: str) -> list[int]:
    # @TODO i believe we can remove everything between {} as it states that the alternatives beteen the brackets are equally ranked, and every occasion happens at the end
    ballot = ballot.strip()  # removes any whitespaces or newline characters

    ballot = re.sub(r',{.*?}', '', ballot)  # removes everything between {} ,

    ballot_str = ballot.split(',')  # make list

    ballot_int = [int(x) for x in ballot_str]  # convert to int
    return ballot_int


def manipulate_ballot_1(profiles: list[Profile]):
    manip_count = 0
    for profile in profiles:
        if 1 in profile.ballot and 4 in profile.ballot and len(
                profile.ballot) > 2:  # in the case where it ranks 4 as well
            if profile.ballot.index(1) == 0:
                continue

            if profile.ballot.index(4) > profile.ballot.index(1) > 0:
                # print(profile.ballot, end="->")
                profile.ballot.remove(1)
                profile.ballot.insert(0, 1)
                manip_count += profile.count
                # print(profile.ballot)

        elif 1 in profile.ballot:
            if profile.ballot.index(1) > 0:
                print(profile.ballot, end="->")
                profile.ballot.remove(1)
                profile.ballot.insert(0, 1)
                manip_count += profile.count
                print(profile.ballot)

    print(manip_count)


def extract_data() -> list[Profile]:
    """ function to read and extract data from the dataset
        :return dictionary containing nr of votes as key, and ballot as value """

    votes = list()
    with open("dataset_revised.txt", "r") as file:
        for line in file:
            data_parts = line.split(":")  # split count from ballot
            count = int(data_parts[0])
            ballot = data_parts[1]
            ballot = format_ballot(ballot)

            votes.append(Profile(ballot, count))

    return votes


def plurality_round(votes: list[Profile], available_alternatives: list[int]) -> dict[int, int]:
    """does 1 round of plurality, then returns a dictionary containing alternative:nr of votes (plurality) """
    alternative_count = dict()
    for alternative in available_alternatives:
        alternative_count[alternative] = 0

    for profile in votes:
        alternative_count[profile.ballot[0]] += profile.count

    return alternative_count


def remove_alternative(vote_profile: list[Profile], alternatives_to_remove: list[int]) -> list[Profile]:
    for alternative in alternatives_to_remove:  # in case of a tie this will run more than once:

        for vote in vote_profile.copy():  # needs copy as we are removing from list
            if alternative in vote.ballot:  # check if alternative is in ballot
                vote.ballot.remove(alternative)

            if len(vote.ballot) == 0:  # remove empty ballots (no longer necessary)
                vote_profile.remove(vote)

    return vote_profile


def print_recap(p_scores: dict[int, int], alternatives: list[int], vote_round: int) -> None:
    print(f"____________________________ vote round: {vote_round} ________________________________________\n"
          f"plurality scores: {p_scores}\n"
          f"alternatives to be removed: {alternatives}\n"
          f"___________________________________________________________________________________\n")


def stv_computations():
    """STV algorithm:
    - calculate plurality scores
    - remove alternative with lowest alternative score (in case of a tie remove both)
    """
    all_alternatives = [x for x in range(1, 12)]  # hardcoded for now

    votes = extract_data()
    vote_round = 1

    while vote_round < 12:
        p_scores = plurality_round(votes=votes, available_alternatives=all_alternatives)

        min_value = min(p_scores.values())
        alternatives = [key for key, value in p_scores.items() if value == min_value]

        for alt in alternatives:
            all_alternatives.remove(alt)

        print_recap(p_scores, alternatives, vote_round)

        votes = remove_alternative(vote_profile=votes, alternatives_to_remove=alternatives)

        if len(alternatives) == len(p_scores):
            break  # winner found

        vote_round += 1


if __name__ == '__main__':
    stv_computations()

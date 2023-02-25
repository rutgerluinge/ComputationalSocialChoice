from dataclasses import dataclass
import re


@dataclass
class Profile:
    """class to contain every row of data """
    ballot: list[int]
    count: int


def format_ballot(ballot: str) -> list[int]:
    # @TODO i believe we can remove everything between {} as it states that the alternatives beteen the brackets are equally ranked, and every occasion happens at the end
    ballot = ballot.strip()  # removes any whitespaces or newline characters

    ballot = re.sub(r',{.*?}', '', ballot)  # removes everything between {} ,

    ballot_str = ballot.split(',')  # make list
    ballot_int = [int(x) for x in ballot_str]  # convert to int
    return ballot_int


def extract_data() -> list[Profile]:
    """ function to read and extract data from the dataset
        :return dictionary containing nr of votes as key, and ballot as value """

    votes = list()
    with open("dataset.txt", "r") as file:
        for line in file:
            data_parts = line.split(":")  # split count from ballot
            count = int(data_parts[0])
            ballot = data_parts[1]
            ballot = format_ballot(ballot)

            votes.append(Profile(ballot, count))

    return votes


def plurality_round(votes: list[Profile]) -> dict[int, int]:
    """does 1 round of plurality, then returns a dictionary containing alternative:nr of votes (plurality) """
    alternative_count = dict()
    for profile in votes:
        top_vote = profile.ballot[0]

        if top_vote in alternative_count:
            alternative_count[top_vote] += profile.count
        else:
            alternative_count[top_vote] = profile.count

    return alternative_count


def remove_alternative(vote_profile: list[Profile], alternatives_to_remove: list[int]) -> list[Profile]:

    for alternative in alternatives_to_remove:  # in case of a tie this will run more than once:
        for vote in vote_profile.copy():
            print(vote.ballot, end="-> ")
            if alternative in vote.ballot:      # check if alternative is in ballot
                vote.ballot.remove(alternative)
            print(vote.ballot)
            if len(vote.ballot) == 0:           # remove empty ballots (no longer necessary)
                vote_profile.remove(vote)

    return vote_profile



def print_recap(p_scores: dict[int, int], alternatives:list[int], vote_round:int) -> None:
    print(f"____________________________ vote round: {vote_round} ________________________________________\n"
          f"plurality scores: {p_scores}\n"
          f"alternatives to be removed: {alternatives}\n"
          f"___________________________________________________________________________________\n")

def print_profiles(votes: list[Profile]):
    for votes in votes:
        print(votes.ballot)

def stv_computations():
    """STV algorithm:
    - calculate plurality scores
    - remove alternative with lowest alternative score (in case of a tie remove both)
    """
    votes = extract_data()
    vote_round = 1

    while True:
        p_scores = plurality_round(votes=votes)

        min_value = min(p_scores.values())
        alternatives = [key for key, value in p_scores.items() if value == min_value]

        print_recap(p_scores, alternatives, vote_round)
        votes = remove_alternative(vote_profile=votes, alternatives_to_remove=alternatives)
        # print_profiles(votes)
        if len(alternatives) == len(p_scores):
            break   #winner found

        vote_round += 1



if __name__ == '__main__':
    stv_computations()

from dataclasses import dataclass
import re


@dataclass
class Profile:
    """class to contain every row of data """
    ballot: list[list[int]]     # [[1], [2], [3], [4,5], [6]]   : 1 > 2 > 3 > 4 = 5 > 6 (thats why 2d list)
    count: int


def format_ballot(ballot: str) -> list:
    """extract good format for ballot from a string"""

    my_list = []
    for x in re.findall('\d+|\{[^}]*\}', ballot):
        if '{' in x:
            sub_list = [int(y) for y in x.strip('{}').split(',')]
            my_list.append(sub_list)
        else:
            my_list.append([int(x)])

    return my_list


# def format_ballot(ballot: str) -> list[int]:
#     # @TODO i believe we can remove everything between {} as it states that the alternatives beteen the brackets are equally ranked, and every occasion happens at the end
#     ballot = ballot.strip()  # removes any whitespaces or newline characters
#
#     ballot = re.sub(r',{.*?}', '', ballot)  # removes everything between {} ,
#
#     ballot_str = ballot.split(',')  # make list
#
#     ballot_int = [int(x) for x in ballot_str]  # convert to int
#     return ballot_int



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


def plurality_round(votes: list[Profile], available_alternatives: list[int]) -> dict[int, float]:
    """does 1 round of plurality, then returns a dictionary containing alternative:nr of votes (plurality) """
    alternative_count = dict()
    for alternative in available_alternatives:
        alternative_count[alternative] = 0

    for profile in votes:
        if len(profile.ballot[0]) == 1:  # should not be doing for [{x,y},z,w]
            alternative_count[profile.ballot[0][0]] += profile.count

        if len(profile.ballot[0]) > 1:  # in case [{1, 2}, 3, 4] -> both 1 and 2 should get 0.5 point per vote
            for idx, alt in enumerate(profile.ballot[0]):
                alternative_count[profile.ballot[0][idx]] += profile.count * (1/len(profile.ballot[0]))

    return alternative_count


def remove_alternative(vote_profile: list[Profile], alternatives_to_remove: list[int]) -> list[Profile]:
    for alternative in alternatives_to_remove:  # in case multiple
        for vote in vote_profile.copy():  # needs copy as we are removing from list
            for alt_ballot in vote.ballot:  # this will almost always run once  {1,2}
                if alternative in alt_ballot: #CHECK if alternative matches ballot index
                    alt_ballot.remove(alternative)
                    if len(alt_ballot) == 0:
                        vote.ballot.remove(alt_ballot)

            if len(vote.ballot) == 0:  # remove empty ballots (no longer necessary)
                vote_profile.remove(vote)

    return vote_profile


def print_recap(p_scores: dict[int, float], alternatives: list[int], vote_round: int) -> None:
    print(f"____________________________ vote round: {vote_round} ________________________________________\n"
          f"plurality scores: {p_scores}\n"
          f"alternatives to be removed: {alternatives}\n"
          f"___________________________________________________________________________________\n")


def stv_computations(votes:list[Profile], nr_of_alt:int, printing:bool) -> list[int]:
    """STV algorithm:
    - calculate plurality scores
    - remove alternative with lowest alternative score (in case of a tie remove both)
    @:return list of integers containing the winner(s) of the vote
    """
    all_alternatives = [x for x in range(1,nr_of_alt+1)]  # hardcoded for now
    vote_round = 1

    while vote_round < 12:
        p_scores = plurality_round(votes=votes, available_alternatives=all_alternatives)

        min_value = min(p_scores.values())
        alternatives = [key for key, value in p_scores.items() if value == min_value]

        if printing:
            print_recap(p_scores, alternatives, vote_round)

        votes = remove_alternative(vote_profile=votes, alternatives_to_remove=alternatives)

        for alt in alternatives:
            all_alternatives.remove(alt)

        if len(alternatives) == len(p_scores):
            return alternatives

        vote_round += 1

    return [0]

if __name__ == '__main__':
    votes = extract_data()
    print(f"winner: {stv_computations(votes, 11, printing=True)}")

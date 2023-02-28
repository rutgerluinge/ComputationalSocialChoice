from dataclasses import dataclass
import re


@dataclass
class Profile:
    """class to contain every row of data """
    ballot: list[list[int]]     # [[1], [2], [3], [4,5], [6]]   : 1 > 2 > 3 > 4 = 5 > 6 (thats why 2d list)
    count: int


def format_ballot3(ballot: str) -> list:
    """nasty way of doing this"""

    my_list = []
    for x in re.findall('\d+|\{[^}]*\}', ballot):
        if '{' in x:
            sub_list = [int(y) for y in x.strip('{}').split(',')]
            my_list.append(sub_list)
        else:
            my_list.append([int(x)])

    return my_list


def format_ballot(ballot: str) -> list[int]:
    # @TODO i believe we can remove everything between {} as it states that the alternatives beteen the brackets are equally ranked, and every occasion happens at the end
    ballot = ballot.strip()  # removes any whitespaces or newline characters

    ballot = re.sub(r',{.*?}', '', ballot)  # removes everything between {} ,

    ballot_str = ballot.split(',')  # make list

    ballot_int = [int(x) for x in ballot_str]  # convert to int
    return ballot_int


def manipulate_ballot_1(profiles: list[Profile], winner_alternative:int = 8, wished_alternative:int = 2):
    manip_count = 0
    for profile in profiles:
        idx_wish = None
        idx_win = None
        for idx, alternative in enumerate(profile.ballot):
            if alternative[0] == wished_alternative:
                idx_wish = idx
            if alternative[0] == winner_alternative:
                idx_win = idx

        if idx_wish is None:
            continue
        if idx_win is None and idx_wish == 0:
            continue
        elif idx_win is None and idx_wish > 0:
            profile.ballot[0], profile.ballot[idx_wish] = profile.ballot[idx_wish], profile.ballot[0] #swap
            manip_count += profile.count
        elif idx_win > idx_wish:
            profile.ballot[0], profile.ballot[idx_wish] = profile.ballot[idx_wish], profile.ballot[0]  # swap
            manip_count += profile.count
        elif idx_wish > idx_win:
            continue


def extract_data() -> list[Profile]:
    """ function to read and extract data from the dataset
        :return dictionary containing nr of votes as key, and ballot as value """

    votes = list()
    with open("dataset_revised.txt", "r") as file:
        for line in file:
            data_parts = line.split(":")  # split count from ballot
            count = int(data_parts[0])
            ballot = data_parts[1]
            ballot = format_ballot3(ballot)

            votes.append(Profile(ballot, count))

    return votes


def plurality_round(votes: list[Profile], available_alternatives: list[int]) -> dict[int, int]:
    """does 1 round of plurality, then returns a dictionary containing alternative:nr of votes (plurality) """
    alternative_count = dict()
    for alternative in available_alternatives:
        alternative_count[alternative] = 0

    for profile in votes:
        if len(profile.ballot[0]) == 1:  # should not be doing for [{x,y},z,w]
            alternative_count[profile.ballot[0][0]] += profile.count

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


def print_recap(p_scores: dict[int, int], alternatives: list[int], vote_round: int) -> None:
    print(f"____________________________ vote round: {vote_round} ________________________________________\n"
          f"plurality scores: {p_scores}\n"
          f"alternatives to be removed: {alternatives}\n"
          f"___________________________________________________________________________________\n")


def stv_computations(votes:list[Profile], nr_of_alt:int) -> list[int]:
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
    #manipulate_ballot_1(profiles=votes, winner_alternative=8, wished_alternative=2)
    print(f"winner: {stv_computations(votes, 11)}")

from STVComputations import stv_computations, extract_data, Profile
from copy import deepcopy


def manipulate_stv() -> None:
    votes: list[Profile] = extract_data()
    winner: list[int] = stv_computations(votes=deepcopy(votes), nr_of_alt=11, printing=False)

    alt = [x for x in range(1, 11 + 1)]
    alt.remove(winner[0])

    # Algorithm
    for alt_no_winner in alt:  # for each non winning alternative
        votes_copy = deepcopy(votes)
        nmr_of_swap_ballots = 0
        for vote_idx, profile in enumerate(votes):  # do swapping and end with svt computation
            swap = False
            save_idx = None
            for idx, ballot_item in enumerate(profile.ballot):
                if ballot_item[0] == winner[0]:
                    swap = False
                    break
                if ballot_item[0] == alt_no_winner:
                    if idx == 0:  # swapping not necessary
                        break
                    save_idx = idx
                    swap = True
                    break

            if swap:

                nmr_of_swap_ballots += 1
                votes_copy[vote_idx].ballot[save_idx], votes_copy[vote_idx].ballot[0] = votes_copy[vote_idx].ballot[0], \
                                                                                        votes_copy[vote_idx].ballot[
                                                                                            save_idx]
                for idx, ballot_item in enumerate(profile.ballot):
                    last_idx = len(profile.ballot) - 1
                    if ballot_item[0] == winner[0]:
                        votes_copy[vote_idx].ballot[idx], votes_copy[vote_idx].ballot[last_idx] = \
                            votes_copy[vote_idx].ballot[last_idx], votes_copy[vote_idx].ballot[idx]

        if stv_computations(votes=votes_copy, nr_of_alt=11, printing=True) != winner:
            print(f"alternative {alt_no_winner} can be manipulated to be the winner")
        else:
            print(f"alternative {alt_no_winner} can't be the winner :(")


if __name__ == '__main__':
    manipulate_stv()

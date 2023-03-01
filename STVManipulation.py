from STVComputations import stv_computations, extract_data, Profile
from copy import deepcopy


def manipulate_stv():
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
            for idx, ballot in enumerate(profile.ballot):
                if ballot[0] == winner[0]:
                    swap = False
                    break
                if ballot[0] == alt_no_winner:
                    if idx == 0:  #swapping not necessary
                        break
                    save_idx = idx
                    swap = True
                    break

            if swap:
                nmr_of_swap_ballots += 1
                #print(votes_copy[vote_idx].ballot, end=" -> ")
                votes_copy[vote_idx].ballot[save_idx], votes_copy[vote_idx].ballot[0] = votes_copy[vote_idx].ballot[0], \
                                                                                        votes_copy[vote_idx].ballot[
                                                                                            save_idx]
                #print(votes_copy[vote_idx].ballot)

        printing = False

        if alt_no_winner == 2:
            printing = True

        if stv_computations(votes=votes_copy, nr_of_alt=11, printing=printing) != winner:
            print(f"alternative {alt_no_winner} can be manipulated to be the winner")
        else:
            print(f"alternative {alt_no_winner} can't be the winner :(")



if __name__ == '__main__':
    manipulate_stv()

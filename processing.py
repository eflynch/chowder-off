
def process_ballot(ballot):
    data = {}
    for line in ballot[1:9]:
        category, significance, a, b, c, d = line.split(",")
        data[category] = {
            "significance": 1 if significance == "" else float(significance),
            "a": 0 if a == "" else float(a),
            "b": 0 if b == "" else float(b),
            "c": 0 if c == "" else float(c),
            "d": 0 if d == "" else float(d),
        }
    return data

def compute_normalized_significances(ballot):
    significance_sum = sum([ballot[category]["significance"] for category in ballot])
    normalized_significance = { category : ballot[category]["significance"]/significance_sum for category in ballot}
    return normalized_significance

def general_significance(ballots):
    significances = []
    for ballot in ballots:
        normalized_significance = compute_normalized_significances(ballot)
        significances.append(normalized_significance)
    
    average_significances = {}
    for category in significances[0].keys():
        category_significance_sum = sum([ballot[category] for ballot in significances])
        average_significances[category] = category_significance_sum / len(significances)
    
    return average_significances

def compute_chowder_score(ballot, chowder, category=None):
    if category is not None:
        return ballot[category][chowder]
    normalized_significance = compute_normalized_significances(ballot)
    score = 0
    for category in ballot:
        score += normalized_significance[category] * ballot[category][chowder]
    return score

def compute_ballot_ordinal(ballot, category=None):
    a = compute_chowder_score(ballot, "a", category)
    b = compute_chowder_score(ballot, "b", category)
    c = compute_chowder_score(ballot, "c", category)
    d = compute_chowder_score(ballot, "d", category)
    ordinals = sorted([("a", a), ("b", b), ("c", c), ("d", d)], key=lambda x : x[1], reverse=True)
    return ordinals


def compute_condorcet_winner(ordinals, category=None):
    print("Results for category:", category if category is not None else "overall")
    if category is not None:
        ordinals = ordinals[category]
    else:
        ordinals = ordinals["overall"]
    # compute the pairwise comparisons
    candidates = ["a", "b", "c", "d"]
    pairwise_comparisons = { (c1, c2) : [0, 0] for c1 in candidates for c2 in candidates if c1 != c2 }
    for ballot in ordinals:
        for i in range(len(ballot)):
            for j in range(i+1, len(ballot)):
                c1, s1 = ballot[i]
                c2, s2 = ballot[j]
                pairwise_comparisons[(c1, c2)][0] += 1
                pairwise_comparisons[(c1, c2)][1] += s1 - s2
                pairwise_comparisons[(c2, c1)][0] -= 1
                pairwise_comparisons[(c2, c1)][1] += s2 - s1
    # compute the schwartz set: 
    schwartz_set = set()
    for candidate in candidates:
        defeated = False
        for other_candidate in candidates:
            if candidate == other_candidate:
                continue
            if pairwise_comparisons[(other_candidate, candidate)][0] > 0:
                defeated = True
                print("        ", candidate, "defeated by", other_candidate, "by margin", pairwise_comparisons[(other_candidate, candidate)][0])
                break
        if not defeated:
            schwartz_set.add(candidate)
    
    if len(schwartz_set) != 1:
        print("    No Condorcet winner found.")
        if len(schwartz_set) == 2:
            print(f"    Schwartz set (tie between two candidates): {schwartz_set}")
            # get winner from head-to-head based on score differential
            candidate1, candidate2 = list(schwartz_set)
            if pairwise_comparisons[(candidate1, candidate2)][1] > 0:
                winner = candidate1
            else:
                winner = candidate2
            print(f"    Score-based tie-break winner: {winner} by {abs(pairwise_comparisons[(candidate1, candidate2)][1])} point margin")
        else:
            print(f"    Schwartz set: {schwartz_set}")
            # get winner from score differential
            min_diff = float("inf")
            weakest_pair = None
            for candidate in schwartz_set:
                total_diff = 0
                for other_candidate in schwartz_set:
                    if candidate == other_candidate:
                        continue
                    diff = pairwise_comparisons[(candidate, other_candidate)][1]
                if diff < min_diff:
                    min_diff = diff
                    weakest_pair = (candidate, other_candidate)
            # break cycle by removing weakest pair
            winner = None
            for candidate in schwartz_set:
                if candidate != weakest_pair[0] and candidate != weakest_pair[1]:
                    if pairwise_comparisons[(weakest_pair[0], candidate)][0] > 0:
                        winner = weakest_pair[0]
                        break
            if winner is None:
                winner = weakest_pair[1]
            print(f"    Condorcet winner after breaking cycle with lowest margin: {winner}")
    else:
        winner = list(schwartz_set)[0]
        print(f"    Condorcet winner: {winner}")
        # compute margin of victory
        mov = float("inf")
        runner_up = None
        for other_candidate in candidates:
            if winner == other_candidate:
                continue
            margin = pairwise_comparisons[(winner, other_candidate)][0]
            if margin < mov:
                mov = margin
                runner_up = other_candidate
        print(f"    Margin of victory: {mov}")
        print(f"    Runner-up: {runner_up}")

    
def main():
    ballots = []
    lines = []
    with open("data.csv") as f:
        lines = f.readlines()

    # group every 10 lines together
    for i in range(0, len(lines), 10):
        group = list(map(lambda x : x.strip(), lines[i:i+10]))
        ballots.append(process_ballot(group))

    categories = [line.split(",")[0] for line in lines[1:9]]

    ordinals = {
        category : [compute_ballot_ordinal(ballot, category) for ballot in ballots] for category in categories
    }
    ordinals["overall"] = [compute_ballot_ordinal(ballot) for ballot in ballots]

    compute_condorcet_winner(ordinals)
    for category in categories:
        compute_condorcet_winner(ordinals, category)
    
    print("General Category Weightings:")
    general_weights = general_significance(ballots)
    for category in general_weights:
        print(f"    {category}: {general_weights[category]:.3f}")


if __name__ == "__main__":
    main()

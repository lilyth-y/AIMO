"""
Math Knowledge Base (Application-First Approach)
- Maps mathematical concepts to their structural applications and story contexts.
- Acts as the blueprint for the 'Story Wrapper'.
"""

MATH_APPLICATIONS = {
    "Geometry": {
        "Power of a Point Theorem": {
            "core_concept": "Relates the lengths of line segments formed by two intersecting lines (chords, secants, or tangents) and a circle. PT^2 = PA * PB.",
            "applications": [
                {
                    "id": "geo_power_point_satellite",
                    "name": "Satellite Signal Range",
                    "structure": "Calculate distance to horizon or signal reach given height above a sphere.",
                    "logic_requirements": ["tangent_secant", "earth_radius"],
                    "story_contexts": [
                        "A satellite orbits at height {h} above a planet of radius {R}. What is the maximum line-of-sight distance?",
                        "From a lighthouse {h} meters tall, how far is the horizon?"
                    ]
                },
                {
                    "id": "geo_power_point_tunnel",
                    "name": "Tunnel Intersection",
                    "structure": "Find meeting point or length of intersecting paths inside a circular boundary.",
                    "logic_requirements": ["intersecting_chords"],
                    "story_contexts": [
                        "Two tunnels intersect inside a circular mountain base. Segments are {a}, {b}, {c}. Find {d}.",
                        "Crossed beams in a circular arena support a roof..."
                    ]
                }
            ]
        },
        "Shoelace Formula": {
            "core_concept": "Calculates the area of a polygon given the coordinates of its vertices.",
            "applications": [
                {
                    "id": "geo_shoelace_land",
                    "name": "Land Surveying",
                    "structure": "Calculate area of a plot defined by (x, y) coordinates.",
                    "logic_requirements": ["vertex_list", "area_calculation"],
                    "story_contexts": [
                        "A farmer's field has corners at coordinates {coords}. What is the total area?",
                        "A robot moves to points {coords}. Calculate the area of the patrol zone."
                    ]
                }
            ]
        }
    },
    "Combinatorics": {
        "Stars and Bars": {
            "core_concept": "Counts ways to distribute n identical objects into k distinct bins.",
            "applications": [
                {
                    "id": "comb_stars_bars_server",
                    "name": "Resource Allocation",
                    "structure": "Distribute N tasks among K servers.",
                    "logic_requirements": ["identical_items", "distinct_bins"],
                    "story_contexts": [
                        "Distributing {n} identical jobs to {k} servers...",
                        "Allocating {n} million dollars budget to {k} departments..."
                    ]
                }
            ]
        },
        "Catalan Numbers": {
            "core_concept": "Counts valid parenthesis structures, triangulations, BSTs.",
            "applications": [
                {
                    "id": "comb_catalan_grid",
                    "name": "Grid Paths",
                    "structure": "Count paths on a grid not crossing the diagonal.",
                    "logic_requirements": ["n_by_n_grid", "diagonal_constraint"],
                    "story_contexts": [
                        "A robot moves from (0,0) to ({n},{n}) without crossing the main diagonal...",
                        "Valid nested code block structures with {n} pairs of brackets..."
                    ]
                }
            ]
        },
        "Inclusion-Exclusion Principle": {
            "core_concept": "|A U B U C| = |A| + |B| + |C| - |A∩B| - ... + |A∩B∩C|",
            "applications": [
                {
                    "id": "comb_inc_exc_survey",
                    "name": "Survey Analysis (설문조사 분석)",
                    "structure": "Given subset sizes, find the intersection of all sets.",
                    "logic_requirements": ["valid_set_sizes", "intersection_constraints"],
                    "story_contexts": [
                        "Club Membership: Students belong to Math, Science, or Art clubs...",
                        "Language Skills: Employees speak English, French, or Spanish...",
                        "Product Ownership: Residents own Car, TV, or Computer..."
                    ]
                }
            ]
        },
        "Pigeonhole Principle": {
            "core_concept": "If n items are put into m containers (n > m), at least one container has >1 item.",
            "applications": [
                {
                    "id": "comb_pigeon_guarantee",
                    "name": "Guaranteed Collision (필연적 충돌)",
                    "structure": "Find min items to pick to guarantee k of same type.",
                    "logic_requirements": ["types_count", "target_k"],
                    "story_contexts": [
                        "Sock Picking: Drawing socks from a drawer in the dark...",
                        "Birthday Paradox: Minimum people to guarantee same birth month..."
                    ]
                }
            ]
        }
    },
    "Number Theory": {
        "Chinese Remainder Theorem (CRT)": {
            "core_concept": "Solving simultaneous congruences with coprime moduli.",
            "applications": [
                {
                    "id": "nt_crt_periodic",
                    "name": "Periodic Synchronization (주기적 동기화)",
                    "structure": "Find smallest T > 0 such that T ≡ r1 (mod m1), T ≡ r2 (mod m2)...",
                    "logic_requirements": ["coprime_moduli", "positive_solution"],
                    "story_contexts": [
                        "Planetary Alignment: Planet A orbits every {m1} years, Planet B every {m2} years...",
                        "Shift Work: Nurse A works every {m1} days, Nurse B every {m2} days...",
                        "Lighthouse Flashes: Light A flashes every {m1} sec, Light B every {m2} sec..."
                    ]
                },
                {
                    "id": "nt_crt_grouping",
                    "name": "Remainder Grouping (나머지와 묶음)",
                    "structure": "Find total N such that N ≡ r1 (mod m1), N ≡ r2 (mod m2)...",
                    "logic_requirements": ["coprime_moduli", "range_limit"],
                    "story_contexts": [
                        "Soldier Formation: When marching in rows of {m1}, {r1} soldiers are left over...",
                        "Fruit Packing: When packing apples into boxes of {m1}, {r1} apples remain..."
                    ]
                }
            ]
        },
        "Linear Diophantine Equations": {
            "core_concept": "Integer solutions to ax + by = c.",
            "applications": [
                {
                    "id": "nt_dioph_currency",
                    "name": "Currency/Coin Exchange (화폐 교환)",
                    "structure": "Find non-negative integers x, y for ax + by = c.",
                    "logic_requirements": ["gcd(a,b) divides c", "non_negative"],
                    "story_contexts": [
                        "Stamps: You have {a}-cent and {b}-cent stamps. How to make exactly {c} cents?",
                        "Coinage: A fictional country uses {a} and {b} unit coins..."
                    ]
                },
                {
                    "id": "nt_dioph_frobenius",
                    "name": "Frobenius Coin Problem (동전 문제)",
                    "structure": "Find the largest integer c that CANNOT be expressed as ax + by.",
                    "logic_requirements": ["coprime(a,b)"],
                    "story_contexts": [
                        "Unpayable Amount: What is the largest amount that cannot be paid using only {a} and {b} coins?",
                        "Chicken McNuggets: Nuggets come in packs of {a} and {b}. What is the largest number you can't buy?"
                    ]
                }
            ]
        },
        "Legendre's Formula": {
            "core_concept": "Finds the exponent of a prime p in n!.",
            "applications": [
                {
                    "id": "nt_legendre_zeros",
                    "name": "Trailing Zeros",
                    "structure": "Calculate number of trailing zeros in n!.",
                    "logic_requirements": ["factorial_n", "count_factors_5"],
                    "story_contexts": [
                        "How many zeros are at the end of {n}! ?",
                        "What is the highest power of {p} that divides {n}! ?"
                    ]
                }
            ]
        }
    },
    "Algebra": {
        "Systems of Linear Equations": {
            "core_concept": "Solving N equations for N variables.",
            "applications": [
                {
                    "id": "alg_sys_mixture",
                    "name": "Mixture/Alloy Problems (혼합물 농도)",
                    "structure": "Combine x amount of A% and y amount of B% to get C%.",
                    "logic_requirements": ["conservation_of_mass"],
                    "story_contexts": [
                        "Chemistry: Mixing {a}% acid solution with {b}% solution...",
                        "Gold Alloys: Mixing {a}-karat gold with {b}-karat gold..."
                    ]
                },
                {
                    "id": "alg_sys_rates",
                    "name": "Work/Rate Problems (일률 문제)",
                    "structure": "1/A + 1/B = 1/Total_Time",
                    "logic_requirements": ["harmonic_mean"],
                    "story_contexts": [
                        "Tank Filling: Pipe A fills in {a} hours, Pipe B in {b} hours...",
                        "Joint Work: Alice takes {a} days, Bob takes {b} days..."
                    ]
                }
            ]
        },
        "AM-GM Inequality": {
            "core_concept": "Arithmetic Mean >= Geometric Mean.",
            "applications": [
                {
                    "id": "alg_amgm_optimization",
                    "name": "Optimization",
                    "structure": "Minimize sum given product constant, or maximize product given sum constant.",
                    "logic_requirements": ["positive_reals"],
                    "story_contexts": [
                        "A box has volume {V}. Minimize surface area...",
                        "Fencing a rectangular field with perimeter {P}. Maximize area..."
                    ]
                }
            ]
        }
    },
    "Probability": {
        "Geometric Probability": {
            "core_concept": "Probability defined by geometric measures.",
            "applications": [
                {
                    "id": "prob_geo_meeting",
                    "name": "Meeting Problem",
                    "structure": "Two people arrive within time window T. Wait time t. Prob of meeting?",
                    "logic_requirements": ["area_ratio"],
                    "story_contexts": [
                        "Alice and Bob arrive between 12:00 and 1:00. They wait 15 mins...",
                        "Signal interference overlap probability..."
                    ]
                }
            ]
        },
        "Linearity of Expectation": {
            "core_concept": "E[X+Y] = E[X] + E[Y].",
            "applications": [
                {
                    "id": "prob_exp_matching",
                    "name": "Matching Problem",
                    "structure": "Expected number of fixed points in a random permutation.",
                    "logic_requirements": ["indicator_variables"],
                    "story_contexts": [
                        "N people get their hats back randomly. Expected number of correct matches?",
                        "Expected number of correct guesses in a multiple choice test..."
                    ]
                }
            ]
        }
    }
}


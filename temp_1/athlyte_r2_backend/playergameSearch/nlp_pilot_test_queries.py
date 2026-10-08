nl_queries = [
	{
        "entity": "player", 
        "query": "Has anyone ever rushed for over 1000 yards and caught for 500 yards in the same season?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Rushing yards net" >= 1000 AND "Reception yards" >= 500'
	    }
    },
    {
        "entity": "player", 
        "query": "Has a QB ever thrown for 4000 yards in a season and stayed under 10 picks?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Total passing yards" >= 4000 AND "Pass interceptions" < 10'	    
	    }
    },
    {
        "entity": "player", 
        "query": "show me everyone with at least one rushing touchdown and one receiving touchdown in a game",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'GAME', 
            "conditions":  '"Rushing TD" >= 1 AND "Receiving TD" = 1'    
	    }
    },
    {
        "entity": "player", 
        "query": "players who filled the stat sheet with 5+ tackles, exactly one sack, and exactly one forced fumble",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'GAME', 
            "conditions":  '"Total Tackles" >= 5 AND "Total Sacks" = 1 AND "Forced fumbles" = 1'
	    }
    },
    {
        "entity": "player", 
        "query": "Show the dual-threat QBs with at least 3000 passing yards and 1000 rushing yards in a season",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Total passing yards" >= 3000 AND "Rushing yards net" = 1000'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Which players have had at least 20 career sacks and two pick sixes?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'CAREER', 
            "conditions":  '"Total Sacks" >= 20 AND "Interception return for TD" >= 2'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Which defenders have racked up at least 200 solo tackles, 20 sacks, and forced 10 fumbles in their careers?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'CAREER', 
            "conditions":  '"Solo Tackles" >= 200 AND "Total Sacks" >= 20 AND "Forced fumbles" >= 10'	    
	    }
    },
    {
        "entity": "player", 
        "query": "ball hawks with 10+ forced fumbles, 5 or more recoveries, and multiple fumble recovery TDs in a season",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Forced fumbles" >= 10 AND "Recovered fumbles" >= 5 AND "fumble return for TD" >= 2'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Anyone come to mind who is blocked three or more punts in their career?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'CAREER', 
            "conditions":  '"Punts blocked by" >= 3'
	    }
    },
    {
        "entity": "player", 
        "query": "What punters have at least 10 kicks inside the 20, 50+ punts in a season, and a bomb of at least 60 yards, in a season?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Punts inside 20" >= 10 AND "Total punts" >= 50 AND "Longest Punt" >= 60'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Who has had a season with at least 40 field goals made and 50 attempts?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Field goals made" >= 40 AND "Field Goal Attempt" >= 50'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Who has had a season where they attempted at least 30 field goals?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Field Goal Attempt" >= 30'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Who has had a season with at least 40 PAT made and 50 attempts?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"PAT kicks made" >= 40 AND "PAT kick attempts" >= 50'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Which return specialists have piled up over 1,000 kick return yards, at least 5 TDs, and 30+ returns in their career?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'CAREER', 
            "conditions":  '"Kickoff return yards" >= 1000 AND "Kickoff return for TD" >= 5 AND "Total kickoff returns" >= 30'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Which players have taken five or more kickoffs to the house in a career?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'CAREER', 
            "conditions":  '"Kickoff return for TD" >= 5'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Who has had a shutdown year with 10 or more passes defended, a few picks, and a pick-six?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Pass break ups" >= 10 AND "Defensive pass interception" >= 2 AND "Total kickoff returns" >= 1'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Which pass rushers have put up multiple QB hurries, a sack, and forced a fumble in one game?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'GAME', 
            "conditions":  '"Quarterback hurries" >= 2 AND "Total Sacks" >= 1 AND "Forced fumbles" >= 1'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Has anyone ever racked up 20 tackles in a game and still gotten a sack?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'GAME', 
            "conditions":  '"Total Tackles" >= 20 AND "Total Sacks" >= 1'    
	    }
    },
    {
        "entity": "player", 
        "query": "Who has had a game where they snagged multiple interceptions?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'GAME', 
            "conditions":  '"Pass interceptions" >= 2'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Which punters have boomed a punt of at least 50 yards in a season?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Longest Punt" >= 50'	    
	    }
    },
    {
        "entity": "player", 
        "query": "who has taken at least five picks to the house in their career?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'CAREER', 
            "conditions":  '"Interception return for TD" >= 5'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Who has had a season where they recovered three or more fumbles?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Recovered fumbles" >= 3'    
	    }
    },
    {
        "entity": "player", 
        "query": "Who has blocked multiple field goals in the same season?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Blocked field goals" >= 2'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Which defenders have had a season with at least 20 tackles for loss, 10 sacks, and 3+ forced fumbles?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Tackles for Loss total" >= 20 AND "Total Sacks" >= 10 AND "Forced fumbles" >= 30'	    
	    }
    },
    {
        "entity": "player", 
        "query": "300 all-purpose yards without coughing up the ball",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'GAME', 
            "conditions":  '"All purpose yards" >= 300 AND "Total number of fumbles" = 0'    
	    }
    },
    {
        "entity": "player", 
        "query": "Defenders with 100+ solo tackles & 10+ sacks in a career",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'CAREER', 
            "conditions":  '"Solo Tackles" >= 100 AND "Total Sacks" >= 10'	    
	    }
    },
    {
        "entity": "player", 
        "query": "defensive playmakers that put up 10+ sacks or forced 3 fumbles in the same season",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Total Sacks" >= 10 OR "Forced Fumbles" >= 3'	    
	    }
    },
    {
        "entity": "player", 
        "query": "Has there ever been a player who intercepted 4 passes and ran 2 back for TDs in the same season?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"Defensive pass interception" >= 4 AND "Interception return for TD" >= 2'	    
	    }
    },
    {
        "entity": "player", 
        "query": "return guys to have taken 3 punts or at least 2 kickoffs to the house in a single year",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'SEASON', 
            "conditions":  '"punt return resulting in a td" >= 3 OR "kickoff return for td" >= 2'    
	    }
    },
    {
        "entity": "player", 
        "query": "Who has made five or more field goals in a game and drilled one from deep, like 50 yards or more?",
        "op": 
        {
            "query_type": "Basic", 
            "entity": "player", 
            "qualifier": {}, 
            "stat_period": 'GAME', 
            "conditions":  '"Field goals made" >= 5 AND "Longest field goal made" >= 50'
        }
    }
]

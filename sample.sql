SELECT

　　a.player AS player, current_date() as now, a.lose AS totallose, b.win AS totalwin, (totallose+totalwin) AS total

FROM

　　( SELECT

　　　　case when winner=houser then challenger when  winner=challenger then houser else 0 end AS player, sum(-point)     AS   lose

　　 FROM

　　　　table

　　GROUP BY player

　　)  AS a

LEFT JOIN

　　(SELECT

　　　　winner AS player , sum(point) AS win

　　FROM

　　　　table

　　GROUP BY

　　　　player) AS b

ON

　　a.player=b.player

UNION

SELECT

　　a.player AS player , a.lose AS totallose, b.win AS totalwin, (totallose+totalwin) AS total

FROM

　　( SELECT

　　　　case when winner=houser then challenger when winner=challenger then houser else 0 end  AS player, sum(-point)     AS   lose

　　 FROM

　　　　table

　　GROUP BY player

　　)  AS a

RIGHT join

　　(SELECT

　　　　winner AS player ,sum(point) AS win

　　FROM

　　　　table

　　GROUP BY

　　　　player) AS b

ON

　　a.player=b.player

ORDER BY total DESC
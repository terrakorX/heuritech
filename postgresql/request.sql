

-- Get the top post per author by interactions / likes
SELECT p.id_auteur, 
       p.id_post, 
       p.titre, 
       p.upvotes, 
       p.date_creation
FROM post p
INNER JOIN (
    SELECT id_auteur, MAX(upvotes) AS max_upvotes -- on extrrait le max des upvotes
    FROM post
    GROUP BY id_auteur
) top_posts ON p.id_auteur = top_posts.id_auteur AND p.upvotes = top_posts.max_upvotes;

-- Get the top post per author and per week by interactions / likes
SELECT 
  p.id_auteur,
  a.name,
  p.id_post,
  p.titre,
  p.upvotes,
  p.date_creation,
  EXTRACT(YEAR FROM p.date_creation) AS year,
  EXTRACT(WEEK FROM p.date_creation) AS week
FROM 
  post p
JOIN 
  auteur a ON p.id_auteur = a.id_auteur
WHERE 
  (p.id_post, EXTRACT(YEAR FROM p.date_creation), EXTRACT(WEEK FROM p.date_creation)) IN ( -- on extrait l'annee et la semaine de la date de creation
    SELECT 
      id_post,
      EXTRACT(YEAR FROM date_creation) AS year,
      EXTRACT(WEEK FROM date_creation) AS week
    FROM 
      post
    WHERE
      id_auteur = p.id_auteur
    ORDER BY 
      upvotes DESC -- pour retirer le meilleur post
    LIMIT 1
  )
ORDER BY 
  p.id_auteur, year, week;

-- Get the top author per number of posts (in the available data set)
select * from (select id_auteur , count(*) as number_post from post p group by id_auteur) as p order by  number_post  desc


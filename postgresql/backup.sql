create table auteur (
	id_auteur varchar(255) PRIMARY KEY,
	name varchar(255),
	date_creation timestamp,
	karma_post int,
	karma_com varchar(255),
	link_profil varchar(255),
	CONSTRAINT unique_id_auteur UNIQUE (id_auteur)
)

create table post (
	id_auteur varchar(255),
	id_post varchar(255) PRIMARY KEY,
	titre varchar(255),
	text text,
	date_creation timestamp,
	upvotes int,
	comments varchar(255),
	type_piece_jointe varchar(255),
	piece_jointe varchar(255),
	CONSTRAINT unique_id_post UNIQUE (id_post)
);
CREATE INDEX index1
ON post (id_post)

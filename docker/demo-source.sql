-- This ID belongs only to the explicit mock collector, not a real account.
INSERT INTO telegram_sources(owner_id,telegram_peer_id,username,title,source_type,detected_type,access_type,capabilities)
VALUES('11111111-1111-1111-1111-111111111111',-1001234567890,'sample_electronics','بازار آزمایشی الکترونیک','broadcast_channel','broadcast_channel','public','{"can_read_history":true,"has_topics":false,"has_discussion":false,"sender_metadata_available":false}')
ON CONFLICT(owner_id,telegram_peer_id)DO NOTHING;

-- Run only after the canonical migration runner; never in postgres initdb.
BEGIN;
INSERT INTO users(id,username,full_name,role)
VALUES('11111111-1111-1111-1111-111111111111','owner','مدیر آزمایشی','buyer')
ON CONFLICT(id) DO NOTHING;
INSERT INTO products(id,name,normalized_name,brand,manufacturer,model,category,attributes,unit,pack_size)
VALUES('22222222-2222-2222-2222-222222222226','سرم نرمال سالین','سرم نرمال سالین','داروسازی ایرانی','داروسازی ایرانی','','healthcare','{}','بطری',1)
ON CONFLICT(id) DO NOTHING;
INSERT INTO product_aliases(product_id,alias,normalized_alias,locale,alias_type)
VALUES('22222222-2222-2222-2222-222222222226','نرمال سالین','نرمال سالین','fa','persian_name')
ON CONFLICT DO NOTHING;
INSERT INTO telegram_sources(owner_id,telegram_peer_id,username,title,source_type,detected_type,access_type,capabilities,external_llm_allowed)
VALUES('11111111-1111-1111-1111-111111111111',-1001234567890,'perso_synthetic_healthcare','بازار آزمایشی سلامت','broadcast_channel','broadcast_channel','public','{"can_read_history":true,"sender_metadata_available":true}',true)
ON CONFLICT(workspace_id,telegram_peer_id) DO NOTHING;
INSERT INTO interests(user_id,product_id,sell_enabled,buy_enabled)
VALUES('11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222226',false,true)
ON CONFLICT DO NOTHING;
COMMIT;

INSERT INTO checkupcenter_checkup_category (id,"name",ext_id,created,updated,description,emoji) VALUES
	 (5,'Чекап для интервального голодания','fasting','2022-03-03 20:41:10.081559+08','2022-04-13 20:17:59.337245+08','Помогает узнать, есть ли противопоказания к интервальному голоданию.','⏰'),
	 (4,'Чекап для похудения','weight_loss','2021-12-29 19:00:45.506329+08','2022-04-13 20:18:52.658152+08','Эти анализы помогут выяснить, получится ли худеть легко и без осложнений для здоровья.','🥗'),
	 (3,'Витамины и минералы','vitamin','2021-12-13 21:40:32.108109+08','2022-04-13 20:19:40.958958+08','Помогает определить дефицит витаминов и минеральных веществ в организме.','💊'),
	 (1,'Общий чекап','main','2021-01-22 01:14:14.658502+08','2022-04-13 20:21:17.555571+08','Помогает выявить основные риски для здоровья. Составляется по рекомендациям ВОЗ с учетом вашего пола, возраста и индивидуальных особенностей.','🔬'),
	 (2,'Пост-ковид чекап','post-covid','2021-01-22 01:13:48.940676+08','2022-04-13 20:20:33.085378+08','Выявляет осложнения после перенесенного коронавируса.','😷'),
	 (6,'Чекап «Здоровый сон»','sleep','2022-07-29 19:30:09.427888+08','2022-07-29 19:30:09.439693+08','Если нарушение сна происходят без видимой причины – сдайте эти анализы','😴');

INSERT INTO checkupcenter_checkup_category_translation (id,language_code,"name",category_id,description) VALUES
	 (17,'en','Intermittent fasting',5,'It helps to know if there are contraindications to intermittent fasting.'),
	 (18,'de','Intervallfasten',5,'Sie helfen herauszufinden, ob es Kontraindikationen für intermittierendes Fasten gibt.'),
	 (19,'pt','Jejum Intermitente',5,'Ajuda a saber se há contraindicações para o jejum intermitente.'),
	 (20,'es','Ayuno Intermitente',5,'Ayuda a saber si hay contraindicaciones para el ayuno intermitente.'),
	 (10,'en','Weight loss checkup',4,'These tests will help you find out if you can lose weight easily and without health complications.'),
	 (11,'de','Checkup zur Gewichtsabnahme',4,'Mit diesen Tests können Sie herausfinden, ob Sie leicht und ohne gesundheitliche Komplikationen abnehmen können.'),
	 (12,'pt','Check-up de perda de peso',4,'Estes testes o ajudarão a descobrir se você pode perder peso facilmente e sem complicações de saúde.'),
	 (13,'es','Checkup pérdida de peso',4,'Estas pruebas le ayudarán a descubrir si puede perder peso fácilmente y sin complicaciones.'),
	 (5,'en','Vitamins and minerals',3,'Helps identify vitamin and mineral deficiencies in the body.'),
	 (6,'de','Vitamine und Mineralien',3,'Hilft bei der Erkennung von Vitamin- und Mineralstoffmangel im Körper.'),
	 (7,'pt','Check-up de vitamina',3,'Ajuda a identificar deficiências de vitaminas e minerais no corpo.'),
	 (14,'es','Vitaminas y minerales',3,'Ayuda a identificar las deficiencias de vitaminas y minerales en el organismo.'),
	 (15,'es','Checkup post-COVID',2,'Identifica las complicaciones derivadas del coronavirus.'),
	 (8,'pt','Check-up pós-covid',2,'Identifica as complicações do coronavírus.'),
	 (4,'de','Post-Covid-Checkup',2,'Erkennen von Komplikationen durch das Coronavirus.'),
	 (2,'en','Post-covid checkup',2,'Identifies complications from coronavirus.'),
	 (16,'es','Chequeo básico',1,'Le ayuda a identificar los principales riesgos de salud. Elaborado según las recomendaciones de la OMS, teniendo en cuenta su sexo, edad y personalidad.'),
	 (9,'pt','Check-up geral',1,'Ajuda a identificar os principais riscos à saúde. Compilado de acordo com as recomendações da OMS, levando em conta seu sexo, idade e personalidade.'),
	 (3,'de','Basis-Checkup',1,'Hilft Ihnen, wichtige Gesundheitsrisiken zu erkennen. Zusammengestellt nach den Empfehlungen der WHO, unter Berücksichtigung Ihres Geschlechts, Alters und Ihrer Persönlichkeit.'),
	 (1,'en','General Checkup',1,'Helps you identify major health risks. Compiled according to WHO recommendations, taking into account your gender, age, and personality.'),
	 (21,'en','Healthy Sleep Checkup',6,'Take these tests if sleep disturbances occur for no apparent reason'),
	 (22,'de','Checkup für gesunden Schlaf',6,'Falls Schlafstörungen ohne ersichtlichen Grund auftreten, machen Sie diese Tests'),
	 (23,'pt','Check-up do sono saudável',6,'Se ocorrerem distúrbios do sono sem motivo aparente, faça estes testes'),
	 (24,'es','Checkup sueño saludable',6,'Si tiene alteraciones del sueño sin ninguna razón aparente, realice estas pruebas');

INSERT INTO checkupcenter_checkup_product_category (id,"name",ext_id,human_part_id,created,updated) VALUES
	 (2,NULL,NULL,40,'2021-01-22 01:09:04.866228+08','2021-01-22 01:09:04.866434+08'),
	 (3,NULL,NULL,45,'2021-01-22 01:09:04.875149+08','2021-01-22 01:09:04.875339+08'),
	 (4,NULL,NULL,41,'2021-01-22 01:09:06.894333+08','2021-01-22 01:09:06.894749+08'),
	 (5,NULL,NULL,51,'2021-01-22 01:09:06.904818+08','2021-01-22 01:09:06.905038+08'),
	 (7,NULL,NULL,6,'2021-01-22 01:09:08.200125+08','2021-01-22 01:09:08.200391+08'),
	 (8,NULL,NULL,33,'2021-01-22 01:09:15.214524+08','2021-01-22 01:09:15.214733+08'),
	 (9,NULL,NULL,47,'2021-01-22 01:09:15.226489+08','2021-01-22 01:09:15.226712+08'),
	 (10,NULL,NULL,44,'2021-01-22 01:09:17.184536+08','2021-01-22 01:09:17.184762+08'),
	 (11,NULL,NULL,42,'2021-01-22 01:09:17.706582+08','2021-01-22 01:09:17.706807+08'),
	 (12,NULL,NULL,43,'2021-01-22 01:09:17.715466+08','2021-01-22 01:09:17.715682+08'),
	 (13,NULL,NULL,46,'2021-01-22 01:09:17.728619+08','2021-01-22 01:09:17.728836+08'),
	 (14,NULL,NULL,24,'2021-01-22 01:09:18.382755+08','2021-01-22 01:09:18.383075+08'),
	 (15,NULL,NULL,49,'2021-02-12 20:52:23.650192+08','2021-02-12 20:52:23.65072+08'),
	 (16,NULL,NULL,48,'2021-02-12 20:52:23.87541+08','2021-02-12 20:52:23.875643+08'),
	 (6,'Онкология','oncology',NULL,'2021-01-22 01:09:08.191085+08','2022-02-09 01:45:43.296047+08'),
	 (1,'Общая диагностика','common',NULL,'2021-01-22 01:09:04.855602+08','2022-02-09 01:45:55.576935+08');

INSERT INTO checkupcenter_checkup_product_category_translation (id,language_code,"name",category_id) VALUES
	 (1,'en','Oncology',6),
	 (2,'en','Common analysis',1),
	 (3,'de','Onkologie',6),
	 (4,'de','Allgemeine Diagnose',1),
	 (5,'pt','Diagnóstico geral',1),
	 (6,'pt','Oncologia',6),
	 (7,'es','Oncología',6),
	 (8,'es','Diagnóstico general',1);

INSERT INTO checkupcenter_checkup_template (id,"name",filters,is_active,created,updated,category_id,is_calculatable,is_base,is_personalized,description) VALUES
	 (16,'Чекап «Здоровый сон»','{"rules": [{"age": [18, 100]}]}',true,'2022-07-29 19:36:35.736174+08','2023-03-22 00:48:56.929173+08',6,true,false,false,'👉 Если нарушение сна происходят без видимой причины – сдайте эти анализы.'),
	 (14,'Чекап для интервального голодания','{"rules": [{"age": [18, 100]}]}',true,'2022-03-03 20:44:02.290339+08','2023-03-22 00:48:56.943779+08',5,true,false,false,'👉 Помогает узнать, есть ли противопоказания к интервальному голоданию.'),
	 (13,'Чекап для похудения','{"rules": [{"age": [18, 100]}]}',true,'2021-12-29 19:02:15.820573+08','2023-03-22 00:48:56.949424+08',4,true,false,false,'👉 Помогает выяснить, получится ли худеть легко и без осложнений для здоровья.'),
	 (12,'Чекап «Витамины и минералы»','{"rules": [{"age": [18, 100]}]}',true,'2021-12-13 21:43:22.414303+08','2023-03-22 00:48:56.954521+08',3,true,false,false,'👉 Помогает определить дефицит витаминов и минеральных веществ в организме.'),
	 (11,'Пост-ковид чекап','{"rules": [{"age": [18, 100]}]}',true,'2021-02-10 21:02:19.431625+08','2023-03-22 00:48:56.959615+08',2,true,false,false,'👉 Эти анализы помогут определить состояние здоровья после перенесенного коронавируса'),
	 (7,'Базовый чекап для женщин 50–65 лет','{"rules": [{"age": [50, 65], "sex": ["F"]}]}',true,'2021-01-22 21:06:29.612735+08','2022-04-20 22:13:16.111086+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (9,'Базовый чекап для женщин старше 65 лет','{"rules": [{"age": [66, 100], "sex": ["F"]}]}',true,'2021-01-22 21:06:29.65963+08','2022-04-20 22:14:17.808493+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (8,'Базовый чекап для мужчин 50–65 лет','{"rules": [{"age": [50, 65], "sex": ["M"]}]}',true,'2021-01-22 21:06:29.63664+08','2022-04-20 22:15:33.041798+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (10,'Базовый чекап для мужчин старше 65 лет','{"rules": [{"age": [66, 100], "sex": ["M"]}]}',true,'2021-01-22 21:06:29.681481+08','2022-04-20 22:16:50.316763+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (15,'Персональный чекап','{"rules": [{"age": [18, 100]}]}',true,'2022-04-13 20:22:53.073154+08','2022-04-13 20:22:53.084822+08',1,true,false,true,'👉 Подбирается по вашим индивидуальным особенностям'),
	 (1,'Базовый чекап для женщин 18–29 лет','{"rules": [{"age": [18, 29], "sex": ["F"]}]}',true,'2021-01-22 21:06:29.448719+08','2022-04-20 21:54:56.802821+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (2,'Базовый чекап для мужчин 18–29 лет','{"rules": [{"age": [18, 29], "sex": ["M"]}]}',true,'2021-01-22 21:06:29.493779+08','2022-04-20 22:00:58.757339+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (5,'Базовый чекап для женщин 40–49 лет','{"rules": [{"age": [40, 49], "sex": ["F"]}]}',true,'2021-01-22 21:06:29.565647+08','2022-04-20 22:09:39.178593+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (6,'Базовый чекап для мужчин 40–49 лет','{"rules": [{"age": [40, 49], "sex": ["M"]}]}',true,'2021-01-22 21:06:29.58867+08','2022-04-20 22:11:18.398456+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (3,'Базовый чекап для женщин 30–39 лет','{"rules": [{"age": [30, 39], "sex": ["F"]}]}',true,'2021-01-22 21:06:29.519032+08','2022-04-20 22:00:23.393819+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья'),
	 (4,'Базовый чекап для мужчин 30–39 лет','{"rules": [{"age": [30, 39], "sex": ["M"]}]}',true,'2021-01-22 21:06:29.542563+08','2022-04-20 22:01:22.991052+08',1,true,true,false,'👉 Бесплатный список анализов составлен по рекомендациям ВОЗ и помогает выявить основные риски для здоровья');

INSERT INTO checkupcenter_checkup_template_translation (id,language_code,"name",template_id,description) VALUES
	 (57,'en','Personalized checkup',15,'👉 Selected according to your individual needs'),
	 (58,'de','Personalisierter Checkup',15,'👉 Ausgewählt nach Ihren individuellen Bedürfnissen'),
	 (59,'pt','Check-up personalizado',15,'👉 Selecionado de acordo com as suas necessidades individuais'),
	 (60,'es','Checkup personalizado',15,'👉 Seleccionado de acuerdo a sus necesidades individuales'),
	 (53,'en','Intermittent fasting checkup',14,'👉 Helps you find out if there are any contraindications to interval fasting.'),
	 (54,'de','Checkup zum Intervallfasten',14,'👉 Hilft Ihnen herauszufinden, ob es Kontraindikationen für das Intervallfasten gibt.'),
	 (55,'pt','Check-up de jejum intermitente',14,'👉 Ajuda você a descobrir se há alguma contraindicação ao jejum intervalado.'),
	 (56,'es','Checkup ayuno intermitente',14,'👉 Le ayuda a saber si hay alguna contraindicación para el ayuno intermitente.'),
	 (36,'en','Weight loss checkup',13,'👉 Helps you find out if you can lose weight easily and without health complications.'),
	 (37,'de','Checkup zur Gewichtsabnahme',13,'👉 Hilft Ihnen herauszufinden, ob Sie leicht und ohne gesundheitliche Komplikationen abnehmen können.'),
	 (38,'pt','Check-up de perda de peso',13,'👉 Ajuda a descobrir se você pode perder peso facilmente e sem complicações para a saúde.'),
	 (39,'es','Checkup pérdida de peso',13,'👉 Le ayuda a saber si puede perder peso fácilmente y sin complicaciones de salud.'),
	 (23,'en','Vitamins and Minerals Checkup',12,'👉 Helps you identify vitamin and mineral deficiencies in your body.'),
	 (24,'de','Vitamine- und Mineralien-Checkup',12,'👉 Hilft Ihnen, Vitamin- und Mineralstoffdefizite in Ihrem Körper zu erkennen.'),
	 (25,'pt','Check-up de vitaminas e minerais',12,'👉 Ajuda você a identificar deficiências de vitaminas e minerais no seu corpo.'),
	 (40,'es','Checkup vitaminas y minerales',12,'👉 Le ayuda a identificar deficiencias de vitaminas y minerales en su organismo.'),
	 (11,'en','Post-covid checkup',11,'👉 These tests will help determine your health status after experiencing coronavirus'),
	 (12,'de','Post-Covid-Checkup',11,'👉 Diese Tests helfen, Ihren Gesundheitszustand nach einer Coronavirus-Erkrankung zu bestimmen'),
	 (26,'pt','Check-up pós-covid',11,'👉 Estes testes ajudarão a determinar seu estado de saúde após a experiência com o coronavírus'),
	 (52,'es','Checkup post-COVID',11,'👉 Estas pruebas ayudarán a determinar su estado de salud después de experimentar el coronavirus'),
	 (10,'en','Basic checkup for men older than 65',10,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (13,'de','Basis-Checkup für Männer über 65 Jahren',10,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (27,'pt','Check-up básico para homens com mais de 65 anos',10,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (41,'es','Checkup básico para hombres de más de 65 años',10,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (9,'en','Basic checkup for women older than 65',9,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (14,'de','Basis-Checkup für Frauen über 65 Jahren',9,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (28,'pt','Check-up básico para mulheres com mais de 65 anos',9,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (42,'es','Checkup básico para mujeres de más de 65 años',9,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (8,'en','Basic checkup for men 50-65 years old',8,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (15,'de','Basis-Checkup für Männer zwischen 50 und 65 Jahren',8,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (29,'pt','Check-up básico para homens 50 a 65',8,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (7,'en','Basic checkup for women 50-65 years old',7,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (6,'en','Basic checkup for men 40-49 years old',6,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (17,'de','Basis-Checkup für Männer zwischen 40 und 49 Jahren',6,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (5,'en','Basic checkup for women 40-49 years old',5,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (18,'de','Basis-Checkup für Frauen zwischen 40 und 49 Jahren',5,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (4,'en','Basic checkup for men 30-39 years old',4,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (19,'de','Basis-Checkup für Männer zwischen 30 und 39 Jahren',4,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (3,'en','Basic checkup for women 30-39 years old',3,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (2,'en','Basic checkup for men 18-29 years old',2,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (21,'de','Basis-Checkup für Männer zwischen 18 und 29 Jahren',2,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (1,'en','Basic checkup for women 18-29 years old',1,'👉 Free test list based on WHO recommendations and helps identify major health risks'),
	 (22,'de','Basis-Checkup für Frauen zwischen 18 und 29 Jahren',1,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (43,'es','Checkup básico para hombres de 50 a 65 años',8,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (16,'de','Basis-Checkup für Frauen zwischen 50 und 65 Jahren',7,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (44,'pt','Check-up básico  para mulheres de 50 a 65 anos',7,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (45,'es','Checkup básico para mujeres de 50 a 65 años',7,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (30,'pt','Check-up básico para homens de 40 a 49 anos',6,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (46,'es','Checkup básico para hombres de 40 a 49 años',6,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (31,'pt','Check-up básico  mulheres de 40 a 49 anos',5,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (47,'es','Checkup básico para mujeres de 40 a 49 años',5,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (32,'pt','Check-up básico para homens de 30 a 39 anos',4,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (48,'es','Checkup básico para hombres de 30 a 39 años',4,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (20,'de','Basis-Checkup für Frauen zwischen 30 und 39 Jahren',3,'👉 Kostenlose Testliste, die auf den Empfehlungen der WHO basiert und hilft, wichtige Gesundheitsrisiken zu erkennen'),
	 (33,'pt','Check-up básico para mulheres de 30 a 39 anos',3,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (49,'es','Checkup básico para mujeres de 30 a 39 años',3,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (34,'pt','Check-up básico para homens de 18 a 29 anos',2,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (50,'es','Checkup básico para hombres de 18 a 29 años',2,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (35,'pt','Check-up básico para mulheres de 18 a 29 anos',1,'👉 Lista de testes gratuita baseada nas recomendações da OMS e ajuda a identificar os principais riscos à saúde'),
	 (51,'es','Checkup básico para mujeres de 18 a 29 años',1,'👉 Lista de pruebas gratuita basada en recomendaciones de la OMS y que ayuda a identificar los principales riesgos para la salud'),
	 (61,'en','Healthy Sleep Checkup',16,'👉 Take these tests if sleep disturbances occur for no apparent reason'),
	 (62,'de','Checkup für gesunden Schlaf',16,'👉 Falls Schlafstörungen ohne ersichtlichen Grund auftreten, machen Sie diese Tests'),
	 (63,'pt','Check-up do sono saudável',16,'👉 Se ocorrerem distúrbios do sono sem motivo aparente, faça estes testes'),
	 (64,'es','Checkup sueño saludable',16,'👉 Si tiene alteraciones del sueño sin ninguna razón aparente, realice estas pruebas');

INSERT INTO checkupcenter_checkup_template_product (id,created,updated,product_id,template_id) VALUES
	 (1,'2021-01-22 21:06:29.476085+08','2021-01-22 21:06:29.476398+08',200,1),
	 (2,'2021-01-22 21:06:29.476141+08','2021-01-22 21:06:29.476428+08',57,1),
	 (137,'2022-07-29 19:36:35.745278+08','2022-07-29 19:36:36.136968+08',82,16),
	 (4,'2021-01-22 21:06:29.507431+08','2021-01-22 21:06:29.507699+08',200,2),
	 (5,'2021-01-22 21:06:29.50746+08','2021-01-22 21:06:29.507729+08',57,2),
	 (138,'2022-07-29 19:36:35.745919+08','2022-07-29 19:36:36.18707+08',274,16),
	 (139,'2022-07-29 19:36:35.746529+08','2022-07-29 19:36:36.188083+08',272,16),
	 (140,'2022-07-29 19:36:35.746937+08','2022-07-29 19:36:36.188805+08',272,16),
	 (9,'2021-01-22 21:06:29.53125+08','2021-01-22 21:06:29.53158+08',200,3),
	 (141,'2022-07-29 19:36:35.747355+08','2022-07-29 19:36:36.189491+08',256,16),
	 (142,'2022-07-29 19:36:35.747762+08','2022-07-29 19:36:36.19022+08',187,16),
	 (12,'2021-01-22 21:06:29.531292+08','2021-01-22 21:06:29.531677+08',57,3),
	 (143,'2022-07-29 19:36:35.748137+08','2022-07-29 19:36:36.190914+08',336,16),
	 (144,'2022-07-29 19:36:35.748484+08','2022-07-29 19:36:36.191476+08',247,16),
	 (145,'2022-07-29 19:36:35.74894+08','2022-07-29 19:36:36.196979+08',192,16),
	 (16,'2021-01-22 21:06:29.553693+08','2021-01-22 21:06:29.553974+08',200,4),
	 (146,'2022-07-29 19:36:35.749334+08','2022-07-29 19:36:36.197836+08',867,16),
	 (19,'2021-01-22 21:06:29.553749+08','2021-01-22 21:06:29.554061+08',57,4),
	 (24,'2021-01-22 21:06:29.5771+08','2021-01-22 21:06:29.577512+08',200,5),
	 (26,'2021-01-22 21:06:29.577126+08','2021-01-22 21:06:29.577568+08',862,5),
	 (28,'2021-01-22 21:06:29.577161+08','2021-01-22 21:06:29.57763+08',57,5),
	 (34,'2021-01-22 21:06:29.600514+08','2021-01-22 21:06:29.60095+08',200,6),
	 (37,'2021-01-22 21:06:29.600571+08','2021-01-22 21:06:29.601016+08',57,6),
	 (44,'2021-01-22 21:06:29.625456+08','2021-01-22 21:06:29.625831+08',200,7),
	 (46,'2021-01-22 21:06:29.625491+08','2021-01-22 21:06:29.625883+08',862,7),
	 (49,'2021-01-22 21:06:29.625538+08','2021-01-22 21:06:29.625948+08',57,7),
	 (53,'2021-01-22 21:06:29.648324+08','2021-01-22 21:06:29.648664+08',355,8),
	 (56,'2021-01-22 21:06:29.648395+08','2021-01-22 21:06:29.648736+08',200,8),
	 (59,'2021-01-22 21:06:29.648438+08','2021-01-22 21:06:29.648801+08',57,8),
	 (63,'2021-01-22 21:06:29.670724+08','2021-01-22 21:06:29.671064+08',200,9),
	 (65,'2021-01-22 21:06:29.67078+08','2021-01-22 21:06:29.671135+08',862,9),
	 (69,'2021-01-22 21:06:29.670831+08','2021-01-22 21:06:29.671254+08',56,9),
	 (70,'2021-01-22 21:06:29.670842+08','2021-01-22 21:06:29.671275+08',57,9),
	 (76,'2021-01-22 21:06:29.694534+08','2021-01-22 21:06:29.694899+08',200,10),
	 (81,'2021-01-22 21:06:29.694608+08','2021-01-22 21:06:29.696613+08',57,10),
	 (85,'2021-02-10 21:02:19.444432+08','2021-02-10 21:02:19.499284+08',50,11),
	 (86,'2021-02-10 21:02:19.445285+08','2021-02-10 21:02:19.505008+08',248,11),
	 (89,'2021-02-10 21:02:19.447075+08','2021-02-10 21:02:19.509045+08',856,11),
	 (91,'2021-02-10 21:02:19.448395+08','2021-02-10 21:02:19.510998+08',57,11),
	 (97,'2021-02-24 21:46:45.651371+08','2021-02-24 21:46:45.738358+08',206,11),
	 (98,'2021-02-24 21:46:45.652073+08','2021-02-24 21:46:45.741257+08',217,11),
	 (99,'2021-12-13 21:43:22.423701+08','2021-12-13 21:43:22.454046+08',79,12),
	 (100,'2021-12-13 21:43:22.424321+08','2021-12-13 21:43:22.456806+08',80,12),
	 (101,'2021-12-13 21:43:22.424853+08','2021-12-13 21:43:22.457453+08',204,12),
	 (102,'2021-12-13 21:43:22.425249+08','2021-12-13 21:43:22.458046+08',81,12),
	 (103,'2021-12-13 21:43:22.426021+08','2021-12-13 21:43:22.458666+08',82,12),
	 (104,'2021-12-13 21:43:22.426606+08','2021-12-13 21:43:22.459252+08',866,12),
	 (105,'2021-12-13 21:43:22.427125+08','2021-12-13 21:43:22.459795+08',88,12),
	 (106,'2021-12-29 19:02:15.828561+08','2021-12-29 19:02:15.845093+08',56,13),
	 (107,'2021-12-29 19:02:15.828983+08','2021-12-29 19:02:15.848203+08',60,13),
	 (108,'2021-12-29 19:02:15.829359+08','2021-12-29 19:02:15.848935+08',180,13),
	 (109,'2022-03-03 20:44:02.300134+08','2022-03-03 20:44:02.329619+08',56,14),
	 (110,'2022-03-03 20:44:02.300676+08','2022-03-03 20:44:02.333599+08',171,14),
	 (111,'2022-03-03 20:44:02.301513+08','2022-03-03 20:44:02.334608+08',170,14),
	 (112,'2022-03-03 20:44:02.301876+08','2022-03-03 20:44:02.335408+08',230,14),
	 (113,'2022-03-03 20:44:02.302233+08','2022-03-03 20:44:02.33603+08',231,14),
	 (114,'2022-03-03 20:44:02.302596+08','2022-03-03 20:44:02.336654+08',60,14),
	 (115,'2022-03-03 20:44:02.303024+08','2022-03-03 20:44:02.337318+08',180,14),
	 (116,'2022-04-20 21:54:56.772303+08','2022-04-20 21:54:56.805906+08',204,1),
	 (117,'2022-04-20 22:00:23.32209+08','2022-04-20 22:00:23.401201+08',204,3),
	 (118,'2022-04-20 22:00:58.706717+08','2022-04-20 22:00:58.762198+08',204,2),
	 (119,'2022-04-20 22:01:22.925272+08','2022-04-20 22:01:22.999708+08',204,4),
	 (120,'2022-04-20 22:09:39.089763+08','2022-04-20 22:09:39.187699+08',204,5),
	 (121,'2022-04-20 22:09:39.090218+08','2022-04-20 22:09:39.192416+08',248,5),
	 (122,'2022-04-20 22:11:05.37481+08','2022-04-20 22:11:05.522725+08',248,6),
	 (123,'2022-04-20 22:11:05.375166+08','2022-04-20 22:11:05.523699+08',56,6),
	 (124,'2022-04-20 22:11:18.292573+08','2022-04-20 22:11:18.401486+08',204,6),
	 (125,'2022-04-20 22:13:16.002115+08','2022-04-20 22:13:16.120229+08',248,7),
	 (126,'2022-04-20 22:13:16.002602+08','2022-04-20 22:13:16.121354+08',56,7),
	 (127,'2022-04-20 22:13:16.0032+08','2022-04-20 22:13:16.122075+08',204,7),
	 (128,'2022-04-20 22:14:17.730153+08','2022-04-20 22:14:17.815544+08',248,9),
	 (129,'2022-04-20 22:14:17.73067+08','2022-04-20 22:14:17.816465+08',204,9),
	 (130,'2022-04-20 22:15:32.941953+08','2022-04-20 22:15:33.050389+08',204,8),
	 (131,'2022-04-20 22:15:32.942354+08','2022-04-20 22:15:33.053546+08',248,8),
	 (132,'2022-04-20 22:15:32.942669+08','2022-04-20 22:15:33.054772+08',56,8),
	 (133,'2022-04-20 22:16:50.217274+08','2022-04-20 22:16:50.331399+08',204,10),
	 (134,'2022-04-20 22:16:50.217785+08','2022-04-20 22:16:50.333057+08',248,10),
	 (135,'2022-04-20 22:16:50.218455+08','2022-04-20 22:16:50.334146+08',355,10),
	 (136,'2022-04-20 22:16:50.21903+08','2022-04-20 22:16:50.335082+08',56,10);

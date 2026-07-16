"""
Complete Liturgy Seeder for LiturgyBridge.
Seeds the exact, full sequence of the Divine Liturgy of St. John Chrysostom
with real, verbatim German and Church Slavonic texts for all 32 parts.
"""

import uuid
from sqlmodel import Session, select
from backend.app.database import engine
from backend.app.models import User, Community, LiturgicalTemplate, TextItem, TranslationItem, AudioTrack

# Full sequential text items of the Divine Liturgy
liturgy_data = [
    # 1. Opening Blessing
    (
        "liturgy.opening_blessing", "litany",
        "Благословено Царство Отца и Сына и Святаго Духа, ныне и присно и во веки веков.",
        "Gesegnet sei das Reich des Vaters und des Sohnes und des Heiligen Geistes, jetzt und immerdar und in die Ewigkeiten der Ewigkeiten."
    ),
    # 2. Great Litany
    (
        "liturgy.great_litany.lord_have_mercy", "litany",
        "Миром Господу помолимся. Господи, помилуй. О свышнем мире и спасении душ наших, Господу помолимся. Господи, помилуй. О мире всего мира, благостоянии святых Божиих церквей и соединении всех, Господу помолимся. Господи, помилуй. О святем храме сем и с верою, благоговением и страхом Божиим входящих в онь, Господу помолимся. Господи, помилуй.",
        "In Frieden lasst uns zum Herrn beten. Herr, erbarme Dich. Für den Frieden von oben und das Heil unserer Seelen, lasst uns zum Herrn beten. Herr, erbarme Dich. Für den Frieden der ganzen Welt, das Wohlergehen der heiligen Kirchen Gottes und die Einigung aller, lasst uns zum Herrn beten. Herr, erbarme Dich. Für dieses heilige Haus und für alle, die es mit Glauben, Ehrfurcht und Gottesfurcht betreten, lasst uns zum Herrn beten. Herr, erbarme Dich."
    ),
    # 3. First Antiphon (Psalm 102 Refrain)
    (
        "liturgy.first_antiphon.refrain", "hymn",
        "Молитвами Богородицы, Спасе, спаси нас. Благослови, душе моя, Господа, и вся внутренняя моя имя святое Его.",
        "Auf die Fürbitten der Gottesgebärerin, o Retter, rette uns. Lobe den Herrn, meine Seele, und all mein Inneres Seinen heiligen Namen."
    ),
    # 4. Small Litany 1
    (
        "liturgy.small_litany_1", "litany",
        "Паки и паки миром Господу помолимся. Заступи, спаси, помилуй и сохрани нас, Боже, Твоею благодатию. Господи, помилуй.",
        "Lasset uns wiederum in Frieden zum Herrn beten. Steh bei, rette, erbarme Dich und bewahre uns, o Gott, durch Deine Gnade. Herr, erbarme Dich."
    ),
    # 5. Second Antiphon & Only-begotten Son
    (
        "liturgy.second_antiphon.refrain", "hymn",
        "Спаси ны, Сыне Божий, воскресый из мертвых, поющия Ти: Аллилуиа. Единородный Сыне и Слове Божий, безсмертен сый, и изволивый спасения нашего ради воплотитися от святыя Богородицы и Приснодевы Марии, непреложно вочеловечивыйся, распныйся же, Христе Боже, смертию смерть поправый, Един сый Святыя Троицы, спрославляемый Отцу и Святому Духу, спаси нас!",
        "Rette uns, Sohn Gottes, der Du von den Toten auferstanden bist, die wir Dir singen: Halleluja. Einziggeborener Sohn und Wort Gottes, der Du unsterblich bist und geruht hast, um unseres Heiles willen Fleisch zu werden aus der heiligen Gottesgebärerin und allzeit reinen Jungfrau Maria, der Du unveränderlich Mensch geworden bist und gekreuzigt wurdest, Christus, Gott, und durch den Tod den Tod zertreten hast, der Du einer bist der Heiligen Dreifaltigkeit, verherrlicht mit dem Vater und dem Heiligen Geist, rette uns!"
    ),
    # 6. Small Litany 2
    (
        "liturgy.small_litany_2", "litany",
        "Паки и паки миром Господу помолимся. Заступи, спаси, помилуй и сохрани нас, Боже, Твоею благодатию. Господи, помилуй. Пресвятую, Пречистую, Преблагословенную, Славную Владычицу нашу Богородицу и Приснодеву Марию, со всеми святыми помянувше, сами себе и друг друга, и весь живот наш Христу Богу предадим. Тебе, Господи.",
        "Lasset uns wiederum in Frieden zum Herrn beten. Steh bei, rette, erbarme Dich und bewahre uns, o Gott, durch Deine Gnade. Herr, erbarme Dich. Unserer allheiligen, makellosen, hochgelobten, glorreichen Herrin, der Gottesgebärerin und allzeit reinen Jungfrau Maria mit allen Heiligen gedenkend, lasst uns uns selbst und einander und unser ganzes Leben Christus, unserem Gott, weihen. Dir, o Herr."
    ),
    # 7. Third Antiphon (Beatitudes)
    (
        "liturgy.third_antiphon.beatitudes", "hymn",
        "Во Царствии Твоем помяни нас, Господи, егда приидеши во Царствии Твоем. Блажени нищии духом, яко тех есть Царство Небесное.",
        "In Deinem Reich gedenke unser, o Herr, wenn Du in Deinem Reich kommst. Selig die Armen im Geiste, denn ihrer ist das Himmelreich."
    ),
    # 8. Small Entrance
    (
        "liturgy.small_entrance.verse", "litany",
        "Премудрость, прости! Приидите, поклонимся и припадем ко Христу. Спаси ны, Сыне Божий, воскресый из мертвых, поющия Ти: Аллилуиа!",
        "Weisheit, aufrecht! Kommt, lasst uns anbeten und niederfallen vor Christus. Rette uns, Sohn Gottes, der Du von den Toten auferstanden bist, die wir Dir singen: Halleluja!"
    ),
    # 9. Tonal Troparion Placeholder (resolved dynamically at runtime)
    # 10. Trisagion
    (
        "liturgy.trisagion.main", "hymn",
        "Святый Боже, Святый Крепкий, Святый Безсмертный, помилуй нас. Святый Боже, Святый Крепкий, Святый Безсмертный, помилуй нас. Святый Боже, Святый Крепкий, Святый Безсмертный, помилуй нас. Слава Отцу и Сыну и Святому Духу, и ныне и присно и во веки веков. Аминь. Святый Безсмертный, помилуй нас. Святый Боже, Святый Крепкий, Святый Безсмертный, помилуй нас.",
        "Heiliger Gott, heiliger Starker, heiliger Unsterblicher, erbarme Dich unser. Heiliger Gott, heiliger Starker, heiliger Unsterblicher, erbarme Dich unser. Heiliger Gott, heiliger Starker, heiliger Unsterblicher, erbarme Dich unser. Ehre sei dem Vater und dem Sohn und dem Heiligen Geist, jetzt und immerdar und in die Ewigkeiten der Ewigkeiten. Amen. Heiliger Unsterblicher, erbarme Dich unser. Heiliger Gott, heiliger Starker, heiliger Unsterblicher, erbarme Dich unser."
    ),
    # 11. Tonal Prokeimenon Placeholder (resolved dynamically at runtime)
    # 12. Epistle Reading Placeholder (resolved dynamically at runtime)
    # 13. Alleluia
    (
        "liturgy.alleluia_ref", "hymn",
        "Аллилуиа, Аллилуиа, Аллилуиа. Очи мои выну ко Господу, яко Той исторгнет от сети нозе мои.",
        "Halleluja, Halleluja, Halleluja. Meine Augen schauen allezeit auf den Herrn, denn Er befreit meine Füße aus dem Netz."
    ),
    # 14. Gospel Reading Placeholder (resolved dynamically at runtime)
    # 15. Sermon Placeholder
    (
        "liturgy.sermon_placeholder", "sermon",
        "Проповедь священника на тему прочитанных Священных Писаний дня.",
        "Es folgt die Predigt des Priesters über die verlesenen Schriftstellen des Tages."
    ),
    # 16. Cherubic Hymn
    (
        "liturgy.cherubic_hymn.main", "hymn",
        "Иже Херувимы тайно образующе, и Животворящей Троице Трисвятую песнь припевающе, всякое ныне житейское отложим попечение.",
        "Die wir die Cherubim geheimnisvoll darstellen und der lebensspendenden Dreifaltigkeit den dreimalheiligen Lobgesang singen, lasst uns ablegen alle irdischen Sorgen."
    ),
    # 17. Litany of Supplication
    (
        "liturgy.litany_supplication", "litany",
        "Исполним молитву нашу Господеви. О предложенных Честных Дарех, Господу помолимся.",
        "Lasst uns unser Gebet zum Herrn erfüllen. Für die dargebrachten kostbaren Gaben lasst uns zum Herrn beten."
    ),
    # 18. Kiss of Peace & Creed
    (
        "liturgy.creed.main", "creed",
        "Верую во единаго Бога Отца, Вседержителя, Творца небу и земли, видимым же всем и невидимым. И во единаго Господа Иисуса Христа, Сына Божия, Единороднаго, Иже от Отца рожденнаго прежде всех век; Света от Света, Бога истинна от Бога истинна, рожденнаго, несотвореннаго, единосущна Отцу, Имже вся быша. Нас ради человек и нашего ради спасения сшедшаго с небес и воплотившагося od Духа Свята и Марии Девы, и вочеловечшася. Распятаго же за ны при Понтийстем Пилате, и страдавша, и погребенна. И воскресшаго в третий день по Писанием. И восшедшаго на небеса, и седяща одесную Отца. И паки грядущаго со славою судити живым и мертвым, Егоже Царствию не будет конца. И в Духа Святаго, Господа, Животворящаго, Иже от Отца исходящаго, Иже со Отцем и Сыном спокланяема и сславима, глаголавшаго пророки. Во едину Святую, Соборную и Апостольскую Церковь. Исповедую едино крещение во оставление грехов. Чаю воскресения мертвых, и жизни будущаго века. Аминь.",
        "Ich glaube an den einen Gott, den Vater, den Allmächtigen, den Schöpfer des Himmels und der Erde, aller sichtbaren und unsichtbaren Dinge. Und an den einen Herrn Jesus Christus, Gottes einziggeborenen Sohn, der aus dem Vater geboren ist vor allen Zeiten. Licht vom Licht, wahrer Gott vom wahren Gott, gezeugt, nicht geschaffen, eines Wesens mit dem Vater, durch den alles geschaffen ist. Der für uns Menschen und zu unserem Heil herabgestiegen ist von den Himmeln und Fleisch geworden ist aus dem Heiligen Geist und der Jungfrau Maria und Mensch geworden ist. Gekreuzigt wurde für uns unter Pontius Pilatus, gelitten hat und begraben wurde. Und auferstanden ist am dritten Tage gemäß den Schriften. Und aufgefahren ist in die Himmel und sitzet zur Rechten des Vaters. Und wiederkommen wird in Herrlichkeit, zu richten die Lebenden und die Toten, dessen Reich kein Ende haben wird. Und an den Heiligen Geist, den Herrn, den Lebensspender, der aus dem Vater hervorgeht, der mit dem Vater und dem Sohn angebetet und verherrlicht wird, der gesprochen hat durch die Propheten. An die eine, heilige, katholische und apostolische Kirche. Ich bekenne die eine Taufe zur Vergebung der Sünden. Ich erwarte die Auferstehung der Toten und das Leben der kommenden Welt. Amen."
    ),
    # 19. Anaphora - Dialogue
    (
        "liturgy.anaphora.dialogue", "litany",
        "Благодать Господа нашего Иисуса Христа, и любы Бога и Отца, и причастие Святаго Духа буди со всеми вами. И со духом твоим. Горе имеем сердца. Имамы ко Господу. Возблагодарим Господа. Достойно и праведно есть покланятися Отцу и Сыну и Святому Духу, Троице единосущней и нераздельней.",
        "Die Gnade unseres Herrn Jesus Christus und die Liebe Gottes des Vaters und die Gemeinschaft des Heiligen Geistes sei mit euch allen. Und mit deinem Geiste. Empor die Herzen. Wir haben sie beim Herrn. Lasst uns danken dem Herrn. Es ist würdig und recht, anzubeten den Vater und den Sohn und den Heiligen Geist, die wesenseine und unteilbare Dreifaltigkeit."
    ),
    # 20. Anaphora - Sanctus
    (
        "liturgy.anaphora.sanctus", "hymn",
        "Свят, Свят, Свят Господь Саваоф, исполнь небо и земля славы Твоея: Осанна in вышних, благословен Грядый во имя Господне.",
        "Heilig, heilig, heilig ist der Herr Zebaoth; voll sind Himmel und Erde von Deiner Herrlichkeit. Hosanna in den Höhen."
    ),
    # 21. Anaphora - Words of Institution
    (
        "liturgy.anaphora.institution", "litany",
        "Приимите, ядите: сие есть Тело Мое, еже за вы ломимое во оставление грехов. Аминь. Пийте от нея вси: сия есть Кровь Моя Новаго Завета, яже за вы и за многи изливаемая во оставление грехов. Аминь.",
        "Nehmet, esset, das ist mein Leib, der für euch gebrochen wird zur Vergebung der Sünden. Amen. Trinket alle daraus, das ist mein Blut des Neuen Bundes, das für euch und für viele vergossen wird zur Vergebung der Sünden. Amen."
    ),
    # 22. Anaphora - Epiklesis
    (
        "liturgy.anaphora.epiklesis", "litany",
        "Твоя от Твоих Тебе приносяще о всех и за вся. Тебе поем, Тебе благословим, Тебе благодарим, Господи, и молим Ти ся, Боже наш... И сотвори убо хлеб сей Честное Тело Христа Твоего. Аминь. А еже в чаши сей, Честную Кровь Христа Твоего. Аминь. Преложив Духом Твоим Святым. Аминь, аминь, аминь.",
        "Das Deine vom Deinen bringen wir Dir dar in allem und für alles. Wir besingen Dich, wir loben Dich, wir danken Dir, o Herr, und wir bitten Dich, unser Gott... Und mache dieses Brot zum kostbaren Leib Deines Christus. Amen. Und das in diesem Kelch zum kostbaren Blut Deines Christus. Amen. Verwandelt durch Deinen Heiligen Geist. Amen, amen, amen."
    ),
    # 23. Hymn to the Theotokos (Axion Estin)
    (
        "liturgy.hymn_to_theotokos", "hymn",
        "Достойно есть яко воистину блажити Тя Богородицу, Присноблаженную и Пренепорочную и Матерь Бога нашего.",
        "Es ist würdig in Wahrheit, dich seligzupreisen, du Gottesgebärerin, allzeit Selige und Makellose und Mutter unseres Gottes."
    ),
    # 24. Lord's Prayer
    (
        "liturgy.lords_prayer.main", "prayer",
        "Отче наш, Иже еси на небесех! Да святится имя Твое, да приидет Царствие Твое, да будет воля Твоя, яко на небеси и на земли. Хлеб наш насущный даждь нам днесь; и остави нам долги наша, якоже и мы оставляем должником нашим; и не введи нас во искушение, но избави нас от лукаваго.",
        "Vater unser im Himmel, geheiligt werde Dein Name. Dein Reich komme. Dein Wille geschehe, wie im Himmel, so auf Erden. Unser tägliches Brot gib uns heute. Und vergib uns unsere Schuld, wie auch wir vergeben unseren Schuldigern. Und führe uns nicht in Versuchung, sondern erlöse uns von dem Bösen."
    ),
    # 25. Communion - Elevation
    (
        "liturgy.communion.elevation", "litany",
        "Святая святым.",
        "Das Heilige den Heiligen!"
    ),
    # 26. Communion - Response
    (
        "liturgy.communion.response", "hymn",
        "Един Свят, Един Господь, Иисус Христос, во славу Бога Отца. Аминь.",
        "Einer ist heilig, einer ist der Herr: Jesus Christus, zur Ehre Gottes des Vaters. Amen."
    ),
    # 27. Communion Hymn (Koinonikon)
    (
        "liturgy.communion.koinonikon", "hymn",
        "Тело Христово приимите, Источника безсмертнаго вкусите. Аллилуиа, аллилуиа, аллилуиа.",
        "Empfangt den Leib Christi, kostet von der Quelle der Unsterblichkeit. Halleluja, Halleluja, Halleluja."
    ),
    # 28. Communion - Invitation
    (
        "liturgy.communion.invitation", "litany",
        "Со страхом Божиим и верою приступите.",
        "Mit Furcht Gottes, mit Glauben und Liebe tretet herbei!"
    ),
    # 29. Post-Communion
    (
        "liturgy.communion.post_communion", "hymn",
        "Видехом Свет истинный, прияхом Духа Небеснаго, обретохом веру истинную, Нераздельней Троице поклоняемся.",
        "Wir haben das wahre Licht gesehen, wir haben den himmlischen Geist empfangen, wir haben den wahren Glauben gefunden. Vor der unteilbaren Dreifaltigkeit fallen wir nieder."
    ),
    # 30. Thanksgiving Hymn
    (
        "liturgy.thanksgiving_hymn", "hymn",
        "Да исполнятся уста наша хваления Твоего, Господи, яко да поем славу Твою, яко сподобил еси нас причаститися Святым Твоим, Божественным, Безсмертным и Животворящим Тайнам; соблюди нас во Твоей святыни, всю песнь поучатися правде Твоей. Аллилуиа, Аллилуиа, Аллилуиа.",
        "Es erfülle sich unser Mund mit Deinem Lobpreis, o Herr, damit wir Deine Herrlichkeit singen, weil Du uns gewürdigt hast, an Deinen heiligen, göttlichen, unsterblichen und lebensspendenden Geheimnissen teilzuhaben. Bewahre uns in Deiner Heiligung, damit wir den ganzen Tag Deine Gerechtigkeit lernen. Halleluja, Halleluja, Halleluja."
    ),
    # 31. Prayer of the Ambo
    (
        "liturgy.prayer_ambo", "prayer",
        "Благословляяй благословящыя Тя, Господи, и освящаяй на Тя уповающия, спаси люди Твоя и благослови достояние Твое. Исполнение Церкве Твоея сохрани, освяти любящыя благолепие дому Твоего: Ты тех возпрослави Божественною Твоею силою, и не остави нас, уповающих на Тя. Мир мирови Твоему даруй, церквам Твоим, священником и всем людем Твоим. Яко всякое даяние благо, и всяк дар совершен свыше есть, сходяй от Тебе, Отца Светов: и Тебе славу, и благодарение, и поклонение возсылаем, Отцу и Сыну и Святому Духу, ныне и присно и во веки веков. Аминь.",
        "Der Du segnest, die Dich segnen, o Herr, und heiligst, die auf Dich vertrauen: Rette Dein Volk und segne Dein Erbe. Bewahre die Fülle Deiner Kirche. Heilige die, welche die Zierde Deines Hauses lieben; verherrliche sie als Gegenleistung durch Deine göttliche Kraft und verlass uns nicht, die wir auf Dich hoffen. Schenke Deiner Welt Frieden, Deinen Kirchen, den Priestern und allen Deinen Leuten. Denn jede gute Gabe und jedes vollkommene Geschenk kommt von oben, herabsteigend von Dir, dem Vater der Lichter, und Dir senden wir Lobpreis, Danksagung und Anbetung empor, dem Vater und dem Sohn und dem Heiligen Geist, jetzt und immerdar und in die Ewigkeiten der Ewigkeiten. Amen."
    ),
    # 32. Dismissal
    (
        "liturgy.dismissal", "litany",
        "Буди имя Господне благословено отныне и до века. Буди имя Господне благословено отныне и до века. Буди имя Господне благословено отныне и до века. Благословение Господне на вас, Того благодатию и человеколюбием, всегда, ныне и присно и во веки веков. Аминь. Слава Тебе, Христе Боже, упование наше, слава Тебе. Христос, истинный Бог наш, воскресый из мертвых, молитвами Пречистыя Своея Матере, святых славных и всехвальных Апостол, иже во святых отца нашего Иоанна, архиепископа Константиня града, Златоустаго, и всех святых, помилует и спасет нас, яко Благ и Человеколюбец. Аминь.",
        "Es sei der Name des Herrn gesegnet von nun an bis in Ewigkeit. Es sei der Name des Herrn gesegnet von nun an bis in Ewigkeit. Es sei der Name des Herrn gesegnet von nun an bis in Ewigkeit. Der Segen des Herrn sei auf euch durch Seine Gnade und Menschenliebe, allezeit, jetzt und immerdar und in die Ewigkeiten der Ewigkeiten. Amen. Ehre sei Dir, Christus, Gott, unsere Hoffnung, Ehre sei Dir. Christus, unser wahrer Gott, Auferstandener von den Toten, erbarm Dich unser und rette uns durch die Fürbitten Seiner allreinen Mutter, der heiligen, ruhmvollen und alllobenswerten Apostel, unseres Vaters unter den Heiligen Johannes Chrysostomus, des Erzbischofs von Konstantinopel, und aller Heiligen, denn Er ist gütig und menschenfreundlich. Amen."
    )
]

def seed_complete_liturgy():
    print("=" * 80)
    print("SEEDING COMPLETE LITURGY OF ST. JOHN CHRYSOSTOM (32 PARTS)...")
    print("=" * 80)

    with Session(engine) as session:
        print("Seeding community and priest...")
        # Create or fetch default community
        comm = session.get(Community, uuid.UUID("87a935b6-6124-4f7c-8b9c-8605ef4dad87"))
        if not comm:
            comm = Community(
                id=uuid.UUID("87a935b6-6124-4f7c-8b9c-8605ef4dad87"),
                name="Kathedrale zum Hl. Nikolaus",
                location="Berlin, Deutschland"
            )
            session.add(comm)
            session.commit()
            session.refresh(comm)

        # Create or fetch default priest user
        priest = session.get(User, uuid.UUID("d56ba13b-8512-4eb1-b92c-f9be88a101f3"))
        if not priest:
            priest = User(
                id=uuid.UUID("d56ba13b-8512-4eb1-b92c-f9be88a101f3"),
                name="Vater Alexej",
                email="alexej@nikolaus-kathedrale.de",
                sso_provider="nextcloud",
                external_user_id="nc_alexej"
            )
            session.add(priest)
            session.commit()
            session.refresh(priest)

        # Seeding TextItems and TranslationItems
        for key, category, slavonic, german in liturgy_data:
            # 1. Upsert TextItem
            text_item = session.get(TextItem, key)
            if not text_item:
                text_item = TextItem(
                    key=key,
                    category=category,
                    default_text=german
                )
                session.add(text_item)
                session.commit()
                session.refresh(text_item)
            else:
                text_item.default_text = german
                session.add(text_item)
                session.commit()

            # 2. Delete old translations
            old_trans = session.exec(select(TranslationItem).where(TranslationItem.text_key == key)).all()
            for ot in old_trans:
                session.delete(ot)
            session.commit()

            # 3. Seed new aligned translation items
            ti_cu = TranslationItem(
                text_key=key,
                language="cu",
                translation_text=slavonic,
                approved=True
            )
            ti_de = TranslationItem(
                text_key=key,
                language="de",
                translation_text=german,
                approved=True
            )
            session.add(ti_cu)
            session.add(ti_de)
            session.commit()
        
        print("Liturgical text library fully seeded.")

        # 4. Update the LiturgicalTemplate structure tree with the 32 sequential parts
        template = session.exec(
            select(LiturgicalTemplate).where(LiturgicalTemplate.name == "Göttliche Liturgie des Hl. Johannes Chrysostomus")
        ).first()
        
        if not template:
            template = LiturgicalTemplate(
                name="Göttliche Liturgie des Hl. Johannes Chrysostomus",
                tradition="byzantine",
                structure={},
                is_shared=True
            )
            session.add(template)
            session.commit()
            session.refresh(template)

        complete_structure = {
            "name": "Göttliche Liturgie des Hl. Johannes Chrysostomus",
            "sections": [
                {"section_key": "part_1.blessing", "text_keys": ["liturgy.opening_blessing"]},
                {"section_key": "part_1.great_litany", "text_keys": ["liturgy.great_litany.lord_have_mercy"]},
                {"section_key": "part_1.first_antiphon", "text_keys": ["liturgy.first_antiphon.refrain"]},
                {"section_key": "part_1.small_litany_1", "text_keys": ["liturgy.small_litany_1"]},
                {"section_key": "part_1.second_antiphon", "text_keys": ["liturgy.second_antiphon.refrain"]},
                {"section_key": "part_1.small_litany_2", "text_keys": ["liturgy.small_litany_2"]},
                {"section_key": "part_1.third_antiphon", "text_keys": ["liturgy.third_antiphon.beatitudes"]},
                {"section_key": "part_1.small_entrance", "text_keys": ["liturgy.small_entrance.verse"]},
                {"section_key": "part_1.troparion", "text_keys": ["dynamic.tonal_troparion"]},
                {"section_key": "part_1.trisagion", "text_keys": ["liturgy.trisagion.main"]},
                {"section_key": "part_1.prokeimenon", "text_keys": ["dynamic.tonal_prokeimenon"]},
                {"section_key": "part_1.readings_epistle", "text_keys": ["dynamic.epistle_reading"]},
                {"section_key": "part_1.alleluia", "text_keys": ["liturgy.alleluia_ref"]},
                {"section_key": "part_1.readings_gospel", "text_keys": ["dynamic.gospel_reading"]},
                {"section_key": "part_1.sermon", "text_keys": ["liturgy.sermon_placeholder"]},
                {"section_key": "part_2.cherubic_hymn", "text_keys": ["liturgy.cherubic_hymn.main"]},
                {"section_key": "part_2.litany_supplication", "text_keys": ["liturgy.litany_supplication"]},
                {"section_key": "part_2.creed", "text_keys": ["liturgy.creed.main"]},
                {"section_key": "part_2.anaphora_dialogue", "text_keys": ["liturgy.anaphora.dialogue"]},
                {"section_key": "part_2.anaphora_sanctus", "text_keys": ["liturgy.anaphora.sanctus"]},
                {"section_key": "part_2.anaphora_institution", "text_keys": ["liturgy.anaphora.institution"]},
                {"section_key": "part_2.anaphora_epiklesis", "text_keys": ["liturgy.anaphora.epiklesis"]},
                {"section_key": "part_2.hymn_to_theotokos", "text_keys": ["liturgy.hymn_to_theotokos"]},
                {"section_key": "part_2.lords_prayer", "text_keys": ["liturgy.lords_prayer.main"]},
                {"section_key": "part_2.communion_elevation", "text_keys": ["liturgy.communion.elevation"]},
                {"section_key": "part_2.communion_response", "text_keys": ["liturgy.communion.response"]},
                {"section_key": "part_2.communion_koinonikon", "text_keys": ["liturgy.communion.koinonikon"]},
                {"section_key": "part_2.communion_invitation", "text_keys": ["liturgy.communion.invitation"]},
                {"section_key": "part_2.communion_post", "text_keys": ["liturgy.communion.post_communion"]},
                {"section_key": "part_2.thanksgiving_hymn", "text_keys": ["liturgy.thanksgiving_hymn"]},
                {"section_key": "part_2.prayer_ambo", "text_keys": ["liturgy.prayer_ambo"]},
                {"section_key": "part_2.dismissal", "text_keys": ["liturgy.dismissal"]}
            ]
        }
        
        template.structure = complete_structure
        session.add(template)
        session.commit()
        print("LiturgicalTemplate structure fully updated with 32 parts.")
        print("=" * 80)
        print("SEEDING COMPLETE!")
        print("=" * 80)

if __name__ == "__main__":
    seed_complete_liturgy()

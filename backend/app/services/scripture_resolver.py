"""
LiturgyBridge Dynamic Scripture Resolver.

Fetches daily Epistle/Gospel readings dynamically in multiple languages
(cu, ru, uk, de, en) using the active LLM provider strategy and caches
them in the PostgreSQL database.
"""

import json
import re
from typing import Optional
from sqlmodel import Session, select
from backend.app.models import TextItem, TranslationItem, AudioTrack
from backend.app.services.llm_provider import get_llm_provider
from backend.app.services.tts_provider import get_tts_provider

SCRIPTURE_DATABASE = {
    "Romans 12:1-10": {
        "cu": "Апостол: Римлянам 12:1-10. [1] Молю убо вас, братие, щедротами Божиими, представити телеса ваша жертву живу, святу, благоугодну Богови, словесное служение ваше: [2] и не сообразуйтеся веку сему, но преобразуйтеся обновлением ума вашего, во еже искушати вам, что есть воля Божия благая и угодная и совершенная. [3] Глаголю бо благодатию давшеюся мне, всякому сущему в вас: не мудрствовати паче, еже подобает мудрствовати, но мудрствовати в целомудрии, комуждо якоже Бог разделил есть меру веры. [4] Якоже бо во единем телеси многи уды имамы, уды же вси не тожде деют: [5] тако много части един тело есмы о Христе, а по единому друг другу уди. [6] Имуще же дарования по благодати данней нам различна: аще пророчество, по мере веры; [7] аще ли служение, в служении; аще ли учай, во учении; [8] аще ли утешаяй, во утешении; преподаяй, в простоте; предстояй, со тщанием; милуяй, с добрым изволением. [9] Любы нелицемерна, ненавидяще злаго, прилепляйтеся благому. [10] Братолюбием друг ко другу любезни, честию друг друга предваряюще.",
        "ru": "Итак умоляю вас, братия, милосердием Божиим, представьте тела ваши в жертву живую, святую, благоугодную Богу, для разумного служения вашего, [2] и не сообразуйтесь с веком сим, но преобразуйтесь обновлением ума вашего, чтобы вам познавать, что есть воля Божия, благая, угодная и совершенная. [3] По данной мне благодати, всякому из вас говорю: не думайте о себе более, нежели должно думать; но думайте скромно, по мере веры, какую каждому Бог уделил. [4] Ибо, как в одном теле у нас много членов, но не у всех членов одно и то же дело, [5] так мы, многие, составляем одно тело во Христе, а порознь один для другого члены. [6] И как, по данной нам благодати, имеем различные дарования, то, имеешь ли пророчество, пророчествуй по мере веры; [7] имеешь ли служение, пребывай в служении; учитель ли, — в учении; [8] увещатель ли, — увещевай; раздаватель ли, — раздавай в простоте; начальник ли, — начальствуй с усердием; благотворитель ли, — благотвори с радушием. [9] Любовь да будет непритворна; отвращайтесь зла, прилепляйтесь к добру; [10] будьте братолюбивы друг к другу с нежностью; в почтительности предупреждайте друг друга.",
        "uk": "Тож благаю вас, браття, милосердям Божим, — повіддавайте ваші тіла на жертву живу, святу, приємну Богові, як розумну службу вашу, [2] і не стосуйтеся до цього віку, але перемініться відновою вашого розуму, щоб ви пізнавали, що то є воля Божа, — добро, приємність та досконалість. [3] Через дану мені благодать кажу кожному з вас: не думайте про себе більш, ніж належить думати, але думайте скромно, у міру віри, як кожному Бог уділив. [4] Бо як в території тілі маємо багато членів, а всі члени мають не однакове діло, [5] так багато нас — одне тіло в Христі, а кожен поодинці — один одному члени. [6] І ми маємо різні дари, згідно з даною нам благодаттю: коли пророцтво — пророкуй у міру віри; [7] коли служба — будь у службі; коли вчитель — учи; [8] коли втішитель — утішай; хто подає — подавай у простоті; хто головує — головуй із пильністю; хто милосердствує — милосердствуй із радістю. [9] Любов нехай буде нелицемірна; ненавидьте зло, туліться до добра; [10] будьте братолюбні один до одного з ніжністю; випереджайте один одного пошаною.",
        "de": "Epistellesung: Römer 12,1-10.\n[1] Ich ermahne euch nun, Brüder, durch die Erbarmungen Gottes, eure Leiber darzustellen als ein lebendiges, heiliges, Gott wohlgefälliges Opfer, was euer vernünftiger Gottesdienst ist. [2] Und seid nicht gleichförmig dieser Welt, sondern werdet verwandelt durch die Erneuerung eures Sinnes, dass ihr prüfen mögt, was der gute und wohlgefällige und vollkommene Wille Gottes ist. [3] Denn ich sage durch die Gnade, die mir gegeben worden ist, jedem, der unter euch ist, nicht höher von sich zu denken, als zu denken sich gebührt, sondern so zu denken, dass er besonnen sei, wie Gott einem jeden das Maß des Glaubens zugeteilt hat. [4] Denn wie wir in einem Leib viele Glieder haben, aber die Glieder nicht alle dieselbe Tätigkeit haben, [5] so sind wir die vielen ein Leib in Christus, einzeln aber Glieder voneinander. [6] Da wir aber verschiedene Gnadengaben haben nach der uns verliehenen Gnade: es sei Weissagung, so sei sie in Übereinstimmung mit dem Glauben; [7] es sei Dienst, so sei er im Dienen; es sei der da lehrt, in der Lehre; [8] es sei der da ermahnt, in der Ermahnung; der da mitteilt, in Einfalt; der da vorsteht, mit Fleiß; der da Barmherzigkeit übt, mit Freudigkeit. [9] Die Liebe sei ungeuchelt. Verabscheut das Böse, haltet fest am Guten! [10] In der Bruderliebe seid herzlich gegeneinander, in Ehrerbietung einer dem anderen vorangehend.",
        "en": "Epistle Reading: Romans 12:1-10.\n[1] I beseech you therefore, brethren, by the mercies of God, that ye present your bodies a living sacrifice, holy, acceptable unto God, which is your reasonable service. [2] And be not conformed to this world: but be ye transformed by the renewing of your mind, that ye may prove what is that good, and acceptable, and perfect, will of God. [3] For I say, through the grace given unto me, to every man that is among you, not to think of himself more highly than he ought to think; but to think soberly, according as God hath dealt to every man the measure of faith. [4] For as we have many members in one body, and all members have not the same office: [5] so we, being many, are one body in Christ, and every one members one of another. [6] Having then gifts differing according to the grace that is given to us, whether prophecy, let us prophesy according to the proportion of faith; [7] or ministry, let us wait on our ministering: or he that teacheth, on teaching; [8] or he that exhorteth, on exhortation: he that giveth, let him do it with simplicity; he that ruleth, with diligence; he that sheweth mercy, with cheerfulness. [9] Let love be without dissimulation. Abhor that which is evil; cleave to that which is good. [10] Be kindly affectioned one to another with brotherly love; in honour preferring one another."
    },
    "Matthew 12:1-15": {
        "cu": "Евангелие: Матфея 12:1-15. [1] Во время оно, иде Иисус в субботы сквозе сеяния: ученицы же Его взалкаша и начаша восторгати класы и ясти. [2] Фарисее же видевше рекоша Ему: се ученицы Твои творят, егоже не достоит творити в субботу. [3] Он же рече им: несте ли чли, что сотвори Давид, егда взалка сам и иже с ним? [4] Како вниде в дом Божий и хлебы предложения снеде, ихже не достояше ему ясти, ни иже с ним, токмо иереем единем? [5] Или несте чли в законе, яко в субботы священницы в церкви субботы сквернят, и неповинни суть? [6] Глаголю же вам, яко церкве боле есть зде. [7] Аще ли бысте ведали, что есть: милости хощу, а не жертвы, никогдаже убо бысте осуждали неповинных. [8] Господь бо есть и субботы Сын Человеческий. [9] И прешед оттуду, прииде на сонмище их. [10] И се человек бяше ту суху имый руку: и вопросиша Его, глаголюще: аще достоит в субботы целити? да обвинят Его. [11] Он же рече им: кто есть от вас человек, иже имать овча едино, и аще впадет сие в субботы в яму, не имет ли е и воздвигнет? [12] Кольми убо лучше есть человек овчате? Темже достоит в субботы добро творити. [13] Тогда глагола человеку: простри руку твою. И простре: и утвердися цела яко другая. [14] Фарисее же шедше совет сотвориша на Него, како Его погубят. [15] Иисус же разумев отъиде оттуду.",
        "ru": "В то время проходил Иисус в субботу засеянными полями; ученики же Его взалкали и начали срывать колосья и есть. [2] Фарисеи, увидев это, сказали Ему: вот, ученики Твои делают, чего не должно делать в субботу. [3] Он же сказал им: разве вы не читали, что сделал Давид, когда взалкал сам и бывшие с ним? [4] как он вошел в дом Божий и ел хлебы предложения, которых не должно было есть ни ему, ни бывшим с ним, а только одним священникам? [5] Или не читали ли вы в законе, что в субботы священники в храме нарушают субботу, однако невиновны? [6] Но говорю вам, что здесь Тот, Кто больше храма; [7] если бы вы знали, что значит: «милости хочу, а не жертвы», то не осудили бы невиновных, [8] ибо Сын Человеческий есть господин и субботы. [9] И, отойдя оттуда, вошел Он в синагогу их. [10] И вот, там был человек, имеющий сухую руку. И спросили Иисуса, чтобы обвинить Его: можно ли исцелять в субботы? [11] Он же сказал им: кто из вас, имея одну овцу, если она в субботу упадет в яму, не возьмет ее и не вытащит? [12] Сколько же лучше человек овцы! Итак, можно в субботы делать добро. [13] Тогда говорит человеку тому: протяни руку твою. И он протянул, и стала она здорова, как другая. [14] Фарисеи же, выйдя, имели совещание против Него, как бы погубить Его. [15] Но Иисус, узнав, удалился оттуда.",
        "uk": "Того часу проходив Ісус у суботу засіяними полями; а учні Його зголодніли і почали зривати колосся та їсти. [2] Фарисеї, побачивши це, сказали Йому: «Ось учні Твої роблять те, чого не дозволено робити в суботу». [3] Він же сказав їм: «Хіба ви не читали, що зробив Давид, коли зголоднів сам і ті, що були з ним? [4] Як він увійшов у дім Божий і їв хліби покладання, яких не дозволено було їсти ні йому, ні тим, що були з ним, а тільки самим священикам? [5] Або чи ви не читали в Законі, що в суботу священики в храмі порушують суботу, і однак вони безвинні? [6] Кажу ж вам, що тут Хтось більший, ніж храм. [7] І якби ви знали, що означає: „Милости хочу, а не жертви“, то не засудили б безвинних. [8] Бо Син Людський є Господар і суботи». [9] І, відійшовши звідти, увійшов Він до їхньої синагоги. [10] І ось, був там чоловік, який мав суху руку. І запитали Його, щоб звинуватити Його: «Чи дозволено зціляти в суботу?» [11] Він же сказав їм: «Хто з вас, маючи одну вівцю, якщо вона в суботу впаде в яму, не візьме її й не витягне? [12] А скільки ж людина краща за вівцю! Отже, дозволено в суботу добро робити». [13] Тоді каже чоловікові тому: «Простягни руку твою». І він простяг, і стала вона здорова, як друга. [14] Фарисеї ж, вийшовши, мали нараду проти Нього, як би погубити Його. [15] Та Ісус, дізнавшись, відійшов звідти.",
        "de": "Evangelienlesung: Matthäus 12,1-15.\n[1] Zu jener Zeit ging Jesus am Sabbat durch die Kornfelder; seine Jünger aber waren hungrig, fingen an, Ähren abzurupfen und zu essen. [2] Als das die Pharisäer sahen, sprachen sie zu ihm: Siehe, deine Jünger tun, was am Sabbat nicht erlaubt ist. [3] Er aber sprach zu ihnen: Habt ihr nicht gelesen, was David tat, als ihn und seine Gefährten hungerte? [4] Wie er in das Haus Gottes ging und die Schaubrote aß, die doch weder er noch seine Gefährten essen durften, sondern allein die Priester? [5] Oder habt ihr nicht gelesen im Gesetz, dass am Sabbat die Priester im Tempel den Sabbat brechen und doch ohne Schuld sind? [6] Ich sage euch aber: Hier ist Größeres als der Tempel. [7] Wenn ihr aber wüsstet, was das heißt: »Barmherzigkeit will ich und nicht Opfer«, so hättet ihr die Unschuldigen nicht verurteilt. [8] Denn der Menschensohn ist Herr über den Sabbat. [9] Und er ging von dort weiter und kam in ihre Synagoge. [10] Und siehe, da war ein Mensch, der hatte eine verdorrte Hand. Und sie fragten ihn, um ihn anzuklagen: Ist's auch erlaubt, am Sabbat zu heilen? [11] Er aber sprach zu ihnen: Wer ist unter euch, der eine einzige Schrift hat, und wenn sie ihm am Sabbat in eine Grube fällt, sie nicht ergreift und herauszieht? [12] Wie viel besser ist nun ein Mensch als ein Schaf! Darum darf man am Sabbat Gutes tun. [13] Da sprach er zu dem Menschen: Strecke deine Hand aus! Und er streckte sie aus; und sie wurde ihm wieder gesund wie die andere. [14] Da gingen die Pharisäer hinaus und hielten Rat über ihn, wie sie ihn umbrächten. [15] Aber als Jesus das merkte, wich er von dort.",
        "en": "Gospel Reading: Matthew 12:1-15.\n[1] At that time Jesus went on the sabbath day through the corn; and his disciples were an hungred, and began to pluck the ears of corn, and to eat. [2] But when the Pharisees saw it, they said unto him, Behold, thy disciples do that which is not lawful to do upon the sabbath day. [3] But he said unto them, Have ye not read what David did, when he was an hungred, and they that were with him; [4] how he entered into the house of God, and did eat the shewbread, which was not lawful for him to eat, neither for them which were with him, but only for the priests? [5] Or have ye not read in the law, how that on the sabbath days the priests in the temple profane the sabbath, and are blameless? [6] But I say unto you, That in this place is one greater than the temple. [7] But if ye had known what this meaneth, I will have mercy, and not sacrifice, ye would not have condemned the guiltless. [8] For the Son of man is Lord even of the sabbath day. [9] And when he was departed thence, he went into their synagogue: [10] and, behold, there was a man which had his hand withered. And they asked him, saying, Is it lawful to heal on the sabbath days? that they might accuse him. [11] And he said unto them, What man shall there be among you, that shall have one sheep, and if it fall into a pit on the sabbath day, will he not lay hold on it, and lift it out? [12] How much then is a man better than a sheep? Wherefore it is lawful to do well on the sabbath days. [13] Then saith he to the man, Stretch forth thine hand. And he stretched it forth; and it was restored whole, like as the other. [14] Then the Pharisees went out, and held a council against him, how they might destroy him. [15] But when Jesus knew it, he withdrew himself from thence."
    },
    "Romans 14:1-10": {
        "cu": "Апостол: Римлянам 14:1-10. [1] Немощнаго в вере приемлите, без споров о мнениях. [2] Ибо иной уверен, что можно есть все, а немощный ест овощи. [3] Кто ест, не уничижай того, кто не ест; и кто не ест, не осуждай того, кто ест, потому что Бог принял его. [4] Кто ты, осуждающий чужого раба? Перед своим Господом стоит он, или падает. И будет восставлен, ибо силен Бог восставить его. [5] Иной отличает день от дня, а другой судит о всяком дне равно. Каждый поступай по удостоверению своего ума. [6] Кто различает дни, для Господа различает; и кто не различает дней, для Господа не различает. Кто ест, для Господа ест, ибо благодарит Бога; и кто не ест, для Господа не ест, и благодарит Бога. [7] Ибо никто из нас не живет для себя, и никто не умирает для себя; [8] а живем ли — для Господа живем; умираем ли — для Господа умираем: и потому, живем ли или умираем, — всегда Господни. [9] Ибо Христос для того и умер, и воскрес, и ожил, чтобы господствовать и над мертвыми и над живыми. [10] А ты что осуждаешь брата твоего? Или и ты, что унижаешь брата твоего? Все мы предстанем на суд Христов.",
        "ru": "Немощного в вере принимайте без споров о мнениях. [2] Ибо иной уверен, что можно есть все, а немощный ест овощи. [3] Кто ест, не уничижай того, кто не ест; и кто не ест, не осуждай того, кто ест, потому что Бог принял его. [4] Кто ты, осуждающий чужого раба? Перед своим Господом стоит он, или падает. И будет восставлен, ибо силен Бог восставить его. [5] Иной отличает день от дня, а другой судит о всяком дне равно. Каждый поступай по удостоверению своего ума. [6] Кто различает дни, для Господа различает; и кто не различает дней, для Господа не различает. Кто ест, для Господа ест, ибо благодарит Бога; и кто не ест, для Господа не ест, и благодарит Бога. [7] Ибо никто из нас не живет для себя, и никто не умирает для себя; [8] а живем ли — для Господа живем; умираем ли — для Господа умираем: и потому, живем ли или умираем, — всегда Господни. [9] Ибо Христос для того и умер, и воскрес, и ожил, чтобы господствовать и над мертвыми и над живыми. [10] А ты что осуждаешь брата твоего? Или и ты, что унижаешь брата твоего? Все мы предстанем на суд Христов.",
        "uk": "Слабкого в вірі приймайте, але не для суперечок про погляди. [2] Бо один вірить, що можна їсти все, а слабкий їсть овочі. [3] Хто їсть, нехай не зневажає того, хто не їсть; а хто не їсть, нехай не осуджує того, хто їсть, бо Бог прийняв його. [4] Хто ти такий, що осуджуєш чужого раба? Перед своїм Господом стоїть він або падає. І він буде поставлений, бо Господь має силу поставити його. [5] Один вирізняє день від дня, а інший судить про кожен день однаково. Нехай кожен діє за переконанням власного розуму. [6] Хто зважає на дні, для Господа зважає; а хто не зважає на дні, для Господа не зважає. Хто їсть, для Господа їсть, бо дякує Богові; і хто не їсть, для Господа не їсть, і дякує Богові. [7] Бо ніхто з нас не живе для себе, і ніхто не помирає для себе; [8] а коли живемо — для Господа живемо; коли помираємо — для Господа помираємо: і тому, чи живемо, чи помираємо, — завжди Господні. [9] Бо Христос для того і помер, і воскрес, і ожив, щоб панувати і над мертвими, і над живими. [10] А ти чому осуджуєш брата твого? Або й ти, чому принижуєш брата твого? Усі ми постанемо перед судом Христовим.",
        "de": "Epistellesung: Römer 14,1-10.\n[1] Den Schwachen im Glauben aber nehmt auf, doch nicht zur Entscheidung von Zweifelfragen! [2] Der eine glaubt, alles essen zu dürfen; der Schwache aber isst Gemüse. [3] Wer isst, verachte den nicht, der nicht isst; und wer nicht isst, richte den nicht, der isst; denn Gott hat ihn aufgenommen. [4] Wer bist du, dass du den Hausknecht eines anderen richtest? Er steht oder fällt seinem eigenen Herrn. Er wird aber aufrecht gehalten werden, denn der Herr vermag ihn aufrecht zu halten. [5] Der eine macht Unterschied zwischen Tag und Tag, der andere aber hält jeden Tag gleich. Jeder sei in seinem eigenen Sinn völlig überzeugt! [6] Wer auf den Tag achtet, achtet darauf dem Herrn; und wer isst, isst dem Herrn, denn er dankt Gott; und wer nicht isst, isst dem Herrn nicht und dankt Gott. [7] Denn keiner von uns lebt sich selbst, und keiner stirbt sich selbst. [8] Denn sei es, dass wir leben, wir leben dem Herrn; sei es, dass wir sterben, wir sterben dem Herrn. Sei es nun, dass wir leben, sei es, dass wir sterben, wir sind des Herrn. [9] Denn dazu ist Christus gestorben und wieder lebendig geworden, dass er sowohl über Toten als auch über Lebenden herrsche. [10] Du aber, was richtest du deinen Bruder? Oder auch du, was verachtest du deinen Bruder? Denn wir werden alle vor den Richterstuhl Gottes gestellt werden.",
        "en": "Epistle Reading: Romans 14:1-10.\n[1] Him that is weak in the faith receive ye, but not to doubtful disputations. [2] For one believeth that he may eat all things: another, who is weak, eateth herbs. [3] Let not him that eateth despise him that eateth not; and let not him which eateth not judge him that eateth: for God hath received him. [4] Who art thou that judgest another man's servant? to his own master he standeth or falleth. Yea, he shall be holden up: for God is able to make him stand. [5] One man esteemeth one day above another: another esteemeth every day alike. Let every man be fully persuaded in his own mind. [6] He that regardeth the day, regardeth it unto the Lord; and he that regardeth not the day, to the Lord he doth not regard it. He that eateth, eateth to the Lord, for he giveth God thanks; and he that eateth not, to the Lord he eateth not, and giveth God thanks. [7] For none of us liveth to himself, and no man dieth to himself. [8] For whether we live, we live unto the Lord; and whether we die, we die unto the Lord: whether we live therefore, or die, we are the Lord's. [9] For to this end Christ both died, and rose, and revived, that he might be Lord both of the dead and living. [10] But why dost thou judge thy brother? or why dost thou set at nought thy brother? for we shall all stand before the judgment seat of Christ."
    },
    "Matthew 14:1-15": {
        "cu": "Евангелие: Матфея 14:1-15. [1] Во время оно, услыша Ирод четвертовластник слух Иисусов, [2] и рече отроком своим: сей есть Иоанн Креститель, той воскресе от мертвых, и сего ради силы деются в нем. [3] Ирод бо ем Иоанна, связа его и посади в темницу, Иродиады ради жены Филиппа брата своего. [4] Глаголаше бо ему Иоанн: не достоит тебе имети ея. [5] И хотяше его убити, убояся народа, яко яко пророка его имеяху. [6] День же быв рождества Иродова, пляса дщерь Иродиадина посреде и угоди Иродови. [7] Темже с клятвою обеща ей дати, егоже аще воспросит. [8] Она же, предварена материю своею, рече: даждь ми зде на блюде главу Иоанна Крестителя. [9] И опечалися царь: клятвы же ради и возлежащих с ним, повеле дати ей. [10] И послав усекну Иоанна в темнице. [11] И принесена бысть глава его на блюде, и дана бысть девице, и отнесе матери своей. [12] И приступльше ученицы его, взяша тело его и погребоша е: и пришедше возвестиша Иисусови. [13] И услышав Иисус отъиде оттуду в корабли в пусто место един: и слышавше народи, идоша по Нем пеши от градов. [14] И исшед Иисус виде много народ, и милосердова о них, и исцели недужныя их. [15] Поздне же бывшу, приступиша к Нему ученицы Его, глаголюще: пусто есть место, и час уже мину: отпусти народы, да шедше в веси купят брашна себе.",
        "ru": "В то время Ирод четвертовластник услышал слух об Иисусе [2] и сказал служащим своим: сей есть Иоанн Креститель; он воскрес из мертвых, и потому чудеса делаются им. [3] Ибо Ирод, взяв Иоанна, связал его и посадил в темницу за Иродиаду, жену Филиппа, брата своего, [4] потому что Иоанн говорил ему: не должно тебе иметь ее. [5] И хотел убить его, но боялся народа, потому что его почитали за пророка. [6] Во время же празднования дня рождения Ирода дочь Иродиады плясала перед собранием и угодила Ироду, [7] посему он с клятвою обещал ей дать, чего она ни попросит. [8] Она же, по наущению матери своей, сказала: дай мне здесь на блюде главу Иоанна Крестителя. [9] И опечалился царь, но, ради клятвы и возлежащих с ним, повелел дать ей, [10] и послал отсечь Иоанну голову в темнице. [11] И принесена была голова его на блюде и дана девице, а она отнесла ее матери своей. [12] Ученики же его, придя, взяли тело его и погребли его; и пошли, возвестили Иисусу. [13] И, услышав, Иисус удалился оттуда на лодке в пустынное место один; а народ, услышав о том, пошел за Ним из городов пешком. [14] И, выйдя, Иисус увидел множество людей и сжалился над ними, и исцелил больных их. [15] Когда же настал вечер, приступили к Нему ученики Его и сказали: место здесь пустынное и время уже позднее; отпусти народ, чтобы они пошли в селения и купили себе пищи.",
        "uk": "Того часу почув четвертовласник Ірод про славу Ісуса [2] і сказав слугам своїм: «Це Іван Хреститель; він воскрес із мертвих, і тому чуда діються через нього». [3] Бо Ірод, схопивши Івана, зв’язав його й кинув у темницю через Іродіяду, дружину Пилипа, свого брата, [4] бо Іван казав йому: «Не дозволено тобі мати її». [5] І хотів його вбити, та боявся народу, бо його вважали за пророка. [6] А коли був день народження Ірода, дочка Іродіяди танцювала перед гостями і догодила Іродові. [7] Тому він із клятвою пообіцяв дати їй усе, чого тільки попросить. [8] Вона ж, за порадою своєї матері, сказала: «Дай мені тут на полумиску голову Івана Хрестителя». [9] І засумував цар, але заради клятви і тих, що величалися з ним, повелів дати їй. [10] І послав відрубати Іванові голову в темниці. [11] І принесли голову його на полумиску й дали дівчині, а вона віднесла своїй матері. [12] А учні його, прийшовши, взяли тіло його й поховали його; і пішли, сповістили Ісусу. [13] І, почувши, Ісус відплив звідти на човні в пустинне місце один; а люди, почувши про те, пішли за Ним із міст пішки. [14] І, вийшовши, Ісус побачив безліч людей і зглянувся над ними, і зцілив хворих їхніх. [15] Коли ж настав вечір, підійшли до Нього учні Його й сказали: «Місце тут пустинне і час уже пізній; відпусти людей, щоб пішли по селах та купили собі поживи».",
        "de": "Evangelienlesung: Matthäus 14,1-15.\n[1] Zu jener Zeit hörte der Landesfürst Herodes die Kunde von Jesus [2] und sprach zu seinen Knechten: Dieser ist Johannes der Täufer; er ist auferstanden von den Toten, und darum wirken die Kräfte in ihm. [3] Denn Herodes hatte Johannes ergriffen, ihn gebunden und ins Gefängnis gelegt wegen Herodias, der Frau seines Bruders Philippus. [4] Denn Johannes hatte zu ihm gesagt: Es ist dir nicht erlaubt, sie zu haben. [5] Und er wollte ihn töten, fürchtete aber das Volk, weil sie ihn für einen Propheten hielten. [6] Als aber der Geburtstag des Herodes gefeiert wurde, tanzte die Tochter der Herodias vor den Gästen; und sie gefiel dem Herodes. [7] Darum versprach er ihr mit einem Eid, ihr zu geben, was sie auch fordern würde. [8] Sie aber, von ihrer Mutter angewiesen, sprach: Gib mir hier auf einer Schale den Kopf Johannes des Täufers! [9] Und der König wurde traurig; doch wegen des Eides und derer, die mit ihm zu Tisch saßen, befahl er, ihn ihr zu geben. [10] Und er sandte hin und ließ Johannes im Gefängnis enthaupten. [11] Und sein Kopf wurde auf einer Schale gebracht und dem Mädchen gegeben; und sie trug ihn zu ihrer Mutter. [12] Und seine Jünger kamen herbei, nahmen den Leichnam und begruben ihn; und sie kamen und verkündeten es Jesus. [13] Und als Jesus es hörte, entwich er von dort mit einem Schiff an einen einsamen Ort besonders. Und als die Volksmengen es hörten, folgten sie ihm zu Fuß aus den Städten. [14] Und als Jesus heraustrat, sah er eine große Volksmenge, und er hatte Erbarmen mit ihnen und heilte ihre Kranken. [15] Als es aber Abend geworden war, traten seine Jünger zu ihm und sprachen: Der Ort ist öde, und die Zeit ist schon fortgeschritten; entlasse die Volksmengen, damit sie in die Dörfer gehen und sich Speise kaufen!",
        "en": "Gospel Reading: Matthew 14:1-15.\n[1] At that time Herod the tetrarch heard of the fame of Jesus, [2] and said unto his servants, This is John the Baptist; he is risen from the dead; and therefore mighty works do shew forth themselves in him. [3] For Herod had laid hold on John, and bound him, and put him in prison for Herodias' sake, his brother Philip's wife. [4] For John said unto him, It is not lawful for thee to have her. [5] And when he would have put him to death, he feared the multitude, because they counted him as a prophet. [6] But when Herod's birthday was kept, the daughter of Herodias danced before them, and pleased Herod. [7] Whereupon he promised with an oath to give her whatsoever she would ask. [8] And she, being before instructed of her mother, said, Give me here John Baptist's head in a charger. [9] And the king was sorry: nevertheless for the oath's sake, and them which sat with him at meat, he commanded it to be given her. [10] And he sent, and beheaded John in the prison. [11] And his head was brought in a charger, and given to the damsel: and she brought it to her mother. [12] And his disciples came, and took up the body, and buried it, and went and told Jesus. [13] When Jesus heard of it, he departed thence by ship into a desert place apart: and when the people had heard thereof, they followed him on foot out of the cities. [14] And Jesus went forth, and saw a great multitude, and was moved with compassion toward them, and he healed their sick. [15] And when it was evening, his disciples came to him, saying, This is a desert place, and the time is now past; send the multitude away, that they may go into the villages, and buy themselves victuals."
    }
}

def resolve_scripture_passage(reference_key: str, session: Session) -> Optional[TextItem]:
    """
    Resolves a scripture reference (e.g. 'scripture.epistle.Romans 12:1-10') by fetching
    the passage dynamically in cu, ru, uk, de, and en languages using the active LLM.
    Caches the results in the database and pre-generates the German TTS audio.
    """
    # 1. Parse the actual bible reference (e.g. 'Romans 12:1-10')
    prefix = "scripture.epistle."
    if reference_key.startswith("scripture.gospel."):
        prefix = "scripture.gospel."
    
    bible_ref = reference_key[len(prefix):]
    
    # 2. Check if already exists in DB
    existing = session.get(TextItem, reference_key)
    if existing:
        if bible_ref in SCRIPTURE_DATABASE:
            bible_data = SCRIPTURE_DATABASE[bible_ref]
            for lang, text in bible_data.items():
                already = session.exec(
                    select(TranslationItem).where(
                        TranslationItem.text_key == reference_key,
                        TranslationItem.language == lang
                    )
                ).first()
                if not already:
                    session.add(TranslationItem(text_key=reference_key, language=lang, translation_text=text, approved=True))
                else:
                    already.translation_text = text
                    session.add(already)
            session.commit()
        return existing

    # 3. Call LLM to fetch the scripture in multiple languages
    print(f"Resolving scripture '{bible_ref}' dynamically via LLM...")
    llm = get_llm_provider()
    
    prompt = f"""You are a biblical scholar specializing in Orthodox liturgical texts.
Retrieve the exact scripture passage for the reference: "{bible_ref}".
Provide the text in the following five languages:
1. "cu": The exact Church Slavonic text in Cyrillic script (Elizaveta Bible version).
2. "ru": The Russian Synodal Bible translation.
3. "uk": The Ukrainian translation (Ogienko version).
4. "de": The German translation (Luther or Einheitsübersetzung style).
5. "en": The English translation (King James Version or Orthodox Study Bible style).

Format your response as a strict JSON object with keys "cu", "ru", "uk", "de", and "en".
Do not include any markdown formatting, prefix, or explanation.
Example response:
{{
  "cu": "Святый Боже...",
  "ru": "Святой Боже...",
  "uk": "Святий Боже...",
  "de": "Heiliger Gott...",
  "en": "Holy God..."
}}
"""
    try:
        if bible_ref in SCRIPTURE_DATABASE:
            print(f"Using local pre-seeded database for scripture '{bible_ref}'...")
            bible_data = SCRIPTURE_DATABASE[bible_ref]
        else:
            response_text = llm.generate_text(prompt)
            # Parse JSON from response
            # Strip potential markdown fences if added by LLM
            cleaned_json = response_text.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json[7:]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json[:-3]
            cleaned_json = cleaned_json.strip()
            
            bible_data = json.loads(cleaned_json)
    except Exception as e:
        print(f"Failed to fetch scripture via LLM for ref '{bible_ref}': {str(e)}")
        # Fallback to simple placeholder so the service doesn't crash
        bible_data = {
            "cu": f"Чтение из {bible_ref} (Славянский)",
            "ru": f"Чтение из {bible_ref} (Русский)",
            "uk": f"Читання з {bible_ref} (Українська)",
            "de": f"Lesung aus {bible_ref} (Deutsch)",
            "en": f"Reading from {bible_ref} (English)"
        }

    # 4. Save TextItem in DB
    category = "epistle" if prefix == "scripture.epistle." else "gospel"
    text_item = TextItem(
        key=reference_key,
        category=category,
        default_text=bible_data.get("de", f"Reading {bible_ref}"),
        community_id=None # Global scripture
    )
    session.add(text_item)
    session.commit()
    session.refresh(text_item)

    # 5. Save TranslationItems
    for lang, text in bible_data.items():
        trans_item = TranslationItem(
            text_key=reference_key,
            language=lang,
            translation_text=text,
            approved=True
        )
        session.add(trans_item)
    session.commit()

    # 6. Pre-generate German TTS audio and save as AudioTrack in DB
    try:
        tts = get_tts_provider()
        clean_speech = re.sub(r'\[\d+\]', '', bible_data.get("de", ""))
        audio_bytes = tts.synthesize_speech(clean_speech, "de")
        
        audio_track = AudioTrack(
            text_key=reference_key,
            language="de",
            audio_url="placeholder",
            is_system_default=True,
            is_shared=True,
            description=f"Generated TTS for {reference_key} (de)",
            audio_data=audio_bytes
        )
        session.add(audio_track)
        session.commit()
        session.refresh(audio_track)
        
        audio_track.audio_url = f"/api/v1/liturgy/audio-tracks/{audio_track.id}/stream"
        session.add(audio_track)
        session.commit()
    except Exception as e:
        print(f"Failed to generate TTS audio for scripture {reference_key}: {str(e)}")

    return text_item

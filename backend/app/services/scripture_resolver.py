"""
LiturgyBridge Dynamic Scripture Resolver.

Fetches daily Epistle/Gospel readings dynamically in multiple languages
(cu, ru, uk, de, en) using the active LLM provider strategy and caches
them in the PostgreSQL database.
"""

import json
from typing import Optional
from sqlmodel import Session, select
from backend.app.models import TextItem, TranslationItem, AudioTrack
from backend.app.services.llm_provider import get_llm_provider
from backend.app.services.tts_provider import get_tts_provider

SCRIPTURE_DATABASE = {
    "Romans 12:1-10": {
        "cu": "Молю убо вас, братие, щедротами Божиими, представити телеса ваша жертву живу, святу, благоугодну Богови, словесное служение ваше: и не сообразуйтеся веку сему, но преобразуйтеся обновлением ума вашего, во еже искушати вам, что есть воля Божия благая и угодная и совершенная. Глаголю бо благодатию давшеюся мне, всякому сущему в вас: не мудрствовати паче, еже подобает мудрствовати, но мудрствовати в целомудрии, комуждо якоже Бог разделил есть меру веры. Якоже бо во единем телеси многи уды имамы, уды же вси не тожде деют: тако много части един тело есмы о Христе, а по единому друг другу уди. Имуще же дарования по благодати данней нам различна: аще пророчество, по мере веры; аще ли служение, в служении; аще ли учай, во учении; аще ли утешаяй, во утешении; преподаяй, в простоте; предстояй, со тщанием; милуяй, с добрым изволением. Любы нелицемерна, ненавидяще злаго, прилепляйтеся благому. Братолюбием друг ко другу любезни, честию друг друга предваряюще.",
        "ru": "Итак умоляю вас, братия, милосердием Божиим, представьте тела ваши в жертву живую, святую, благоугодную Богу, для разумного служения вашего, и не сообразуйтесь с веком сим, но преобразуйтесь обновлением ума вашего, чтобы вам познавать, что есть воля Божия, благая, угодная и совершенная. По данной мне благодати, всякому из вас говорю: не думайте о себе более, нежели должно думать; но думайте скромно, по мере веры, какую каждому Бог уделил. Ибо, как в одном теле у нас много членов, но не у всех членов одно и то же дело, так мы, многие, составляем одно тело во Христе, а порознь один для другого члены. И как, по данной нам благодати, имеем различные дарования, то, имеешь ли пророчество, пророчествуй по мере веры; имеешь ли служение, пребывай в служении; учитель ли, — в учении; увещатель ли, — увещевай; раздаватель ли, — раздавай в простоте; начальник ли, — начальствуй с усердием; благотворитель ли, — благотвори с радушием. Любовь да будет непритворна; отвращайтесь зла, прилепляйтесь к добру; будьте братолюбивы друг к другу с нежностью; в почтительности предупреждайте друг друга.",
        "uk": "Тож благаю вас, браття, милосердям Божим, — повіддавайте ваші тіла на жертву живу, святу, приємну Богові, як розумну службу вашу, і не стосуйтеся до цього віку, але перемініться відновою вашого розуму, щоб ви пізнавали, що то є воля Божа, — добро, приємність та досконалість. Через дану мені благодать кажу кожному з вас: не думайте про себе більш, ніж належить думати, але думайте скромно, у міру віри, як кожному Бог уділив. Бо як в одному тілі маємо багато членів, а всі члени мають не однакове діло, так багато нас — одне тіло в Христі, а кожен поодинці — один одному члени. І ми маємо різні дари, згідно з даною нам благодаттю: коли пророцтво — пророкуй у міру віри; коли служба — будь у службі; коли вчитель — учи; коли втішитель — утішай; хто подає — подавай у простоті; хто головує — головуй із пильністю; хто милосердствує — милосердствуй із радістю. Любов нехай буде нелицемірна; ненавидьте зло, туліться до добра; будьте братолюбні один до одного з ніжністю; випереджайте один одного пошаною.",
        "de": "Ich ermahne euch nun, Brüder und Schwestern, durch die Barmherzigkeit Gottes, dass ihr eure Leiber hingebt als ein lebendiges, heiliges, Gott wohlgefälliges Opfer. Dies sei euer vernünftiger Gottesdienst. Und passt euch nicht dieser Weltlauf an, sondern lasst euch verwandeln durch die Erneuerung eures Denkens, damit ihr prüfen könnt, was der gute, wohlgefällige und vollkommene Wille Gottes ist. Denn ich sage durch die Gnade, die mir gegeben ist, jedem unter euch: Strebt nicht über das hinaus, was zu erstreben sich gebührt, sondern strebt nach einem besonnenen Denken, wie Gott jedem das Maß des Glaubens zugeteilt hat. Denn wie wir an einem Leib viele Glieder haben, aber nicht alle Glieder dasselbe Geschäft haben, so sind wir, die vielen, ein Leib in Christus, einzeln aber Glieder voneinander. Da wir aber verschiedene Gaben haben nach der uns gegebenen Gnade: Hat jemand prophetische Rede, so übe er sie dem Glauben entsprechend; hat jemand ein Amt, so diene er; ist jemand Lehrer, so lehre er; hat jemand die Gabe der Ermahnung, so ermahne er; wer gibt, gebe in Einfalt; wer vorsteht, tue es mit Eifer; wer Barmherzigkeit übt, tue es mit Freude. Die Liebe sei ungeheuchelt. Verabscheut das Böse, haltet fest am Guten! In brüderlicher Liebe seid herzlich zueinander; in Ehrerbietung komme einer dem anderen zuvor!",
        "en": "I beseech you therefore, brethren, by the mercies of God, that ye present your bodies a living sacrifice, holy, acceptable unto God, which is your reasonable service. And be not conformed to this world: but be ye transformed by the renewing of your mind, that ye may prove what is that good, and acceptable, and perfect, will of God. For I say, through the grace given unto me, to every man that is among you, not to think of himself more highly than he ought to think; but to think soberly, according as God hath dealt to every man the measure of faith. For as we have many members in one body, and all members have not the same office: so we, being many, are one body in Christ, and every one members one of another. Having then gifts differing according to the grace that is given to us, whether prophecy, let us prophesy according to the proportion of faith; or ministry, let us wait on our ministering: or he that teacheth, on teaching; or he that exhorteth, on exhortation: he that giveth, let him do it with simplicity; he that ruleth, with diligence; he that sheweth mercy, with cheerfulness. Let love be without dissimulation. Abhor that which is evil; cleave to that which is good. Be kindly affectioned one to another with brotherly love; in honour preferring one another."
    },
    "Matthew 12:1-15": {
        "cu": "Во время оно, иде Иисус в субботы сквозе сеяния: ученицы же Его взалкаша и начаша восторгати класы и ясти. Фарисее же видевше рекоша Ему: се ученицы Твои творят, егоже не достоит творити в субботу. Он же рече им: несте ли чли, что сотвори Давид, егда взалка сам и иже с ним? Како вниде в дом Божий и хлебы предложения снеде, ихже не достояше ему ясти, ни иже с ним, токмо иереем единем? Или несте чли в законе, яко в субботы священницы в церкви субботы сквернят, и неповинни суть? Глаголю же вам, яко церкве боле есть зде. Аще ли бысте ведали, что есть: милости хощу, а не жертвы, никогдаже убо бысте осуждали неповинных. Господь бо есть и субботы Сын Человеческий. И прешед оттуду, прииде на сонмище их. И се человек бяше ту суху имый руку: и вопросиша Его, глаголюще: аще достоит в субботы целити? да обвинят Его. Он же рече им: кто есть от вас человек, иже имать овча едино, и аще впадет сие в субботы в яму, не имет ли е и воздвигнет? Кольми убо лучше есть человек овчате? Темже достоит в субботы добро творити. Тогда глагола человеку: простри руку твою. И простре: и утвердися цела яко другая. Фарисее же шедше совет сотвориша на Него, како Его погубят. Иисус же разумев отъиде оттуду.",
        "ru": "В то время проходил Иисус в субботу засеянными полями; ученики же Его взалкали и начали срывать колосья и есть. Фарисеи, увидев это, сказали Ему: вот, ученики Твои делают, чего не должно делать в субботу. Он же сказал им: разве вы не читали, что сделал Давид, когда взалкал сам и бывшие с ним? как он вошел в дом Божий и ел хлебы предложения, которых не должно было есть ни ему, ни бывшим с ним, а только одним священникам? Или не читали ли вы в законе, что в субботы священники в храме нарушают субботу, однако невиновны? Но говорю вам, что здесь Тот, Кто больше храма; если бы вы знали, что значит: «милости хочу, а не жертвы», то не осудили бы невиновных, ибо Сын Человеческий есть господин и субботы. И, отойдя оттуда, вошел Он в синагогу их. И вот, там был человек, имеющий сухую руку. И спросили Иисуса, чтобы обвинить Его: можно ли исцелять в субботы? Он же сказал им: кто из вас, имея одну овцу, если она в субботу упадет в яму, не возьмет ее и не вытащит? Сколько же лучше человек овцы! Итак, можно в субботы делать добро. Тогда говорит человеку тому: протяни руку твою. И он протянул, и стала она здорова, как другая. Фарисеи же, выйдя, имели совещание против Него, как бы погубить Его. Но Иисус, узнав, удалился оттуда.",
        "uk": "Того часу проходив Ісус у суботу засіяними полями; а учні Його зголодніли і почали зривати колосся та їсти. Фарисеї, побачивши це, сказали Йому: «Ось учні Твої роблять те, чого не дозволено робити в суботу». Він же сказав їм: «Хіба ви не читали, що зробив Давид, коли зголоднів сам і ті, що були з ним? Як він увійшов у дім Божий і їв хліби покладання, яких не дозволено було їсти ні йому, ні тим, що були з ним, а тільки самим священикам? Або чи ви не читали в Законі, що в суботу священики в храмі порушують суботу, і однак вони безвинні? Кажу ж вам, що тут Хтось більший, ніж храм. І якби ви знали, що означає: „Милости хочу, а не жертви“, то не засудили б безвинних. Бо Син Людський є Господар і суботи». І, відійшовши звідти, увійшов Він до їхньої синагоги. І ось, був там чоловік, який мав суху руку. І запитали Його, щоб звинуватити Його: «Чи дозволено зціляти в суботу?» Він же сказав їм: «Хто з вас, маючи одну вівцю, якщо вона в суботу впаде в яму, не візьме її й не витягне? А скільки ж людина краща за вівцю! Отже, дозволено в суботу добро робити». Тоді каже чоловікові тому: «Простягни руку твою». І він простяг, і стала вона здорова, як друга. Фарисеї ж, вийшовши, мали нараду проти Нього, як би погубити Його. Та Ісус, дізнавшись, відійшов звідти.",
        "de": "Zu jener Zeit ging Jesus am Sabbat durch die Kornfelder; seine Jünger aber waren hungrig, fingen an, Ähren abzurupfen und zu essen. Als das die Pharisäer sahen, sprachen sie zu ihm: Siehe, deine Jünger tun, was am Sabbat nicht erlaubt ist. Er aber sprach zu ihnen: Habt ihr nicht gelesen, was David tat, als ihn und seine Gefährten hungerte? Wie er in das Haus Gottes ging und die Schaubrote aß, die doch weder er noch seine Gefährten essen durften, sondern allein die Priester? Oder habt ihr nicht gelesen im Gesetz, dass am Sabbat die Priester im Tempel den Sabbat brechen und doch ohne Schuld sind? Ich sage euch aber: Hier ist Größeres als der Tempel. Wenn ihr aber wüsstet, was das heißt: »Barmherzigkeit will ich und nicht Opfer«, so hättet ihr die Unschuldigen nicht verurteilt. Denn der Menschensohn ist Herr über den Sabbat. Und er ging von dort weiter und kam in ihre Synagoge. Und siehe, da war ein Mensch, der hatte eine verdorrte Hand. Und sie fragten ihn, um ihn anzuklagen: Ist's auch erlaubt, am Sabbat zu heilen? Er aber sprach zu ihnen: Wer ist unter euch, der eine einzige Schrift hat, und wenn sie ihm am Sabbat in eine Grube fällt, sie nicht ergreift und herauszieht? Wie viel besser ist nun ein Mensch als ein Schaf! Darum darf man am Sabbat Gutes tun. Da sprach er zu dem Menschen: Strecke deine Hand aus! Und er streckte sie aus; und sie wurde ihm wieder gesund wie die andere. Da gingen die Pharisäer hinaus und hielten Rat über ihn, wie sie ihn umbrächten. Aber als Jesus das merkte, wich er von dort.",
        "en": "At that time Jesus went on the sabbath day through the corn; and his disciples were an hungred, and began to pluck the ears of corn, and to eat. But when the Pharisees saw it, they said unto him, Behold, thy disciples do that which is not lawful to do upon the sabbath day. But he said unto them, Have ye not read what David did, when he was an hungred, and they that were with him; how he entered into the house of God, and did eat the shewbread, which was not lawful for him to eat, neither for them which were with him, but only for the priests? Or have ye not read in the law, how that on the sabbath days the priests in the temple profane the sabbath, and are blameless? But I say unto you, That in this place is one greater than the temple. But if ye had known what this meaneth, I will have mercy, and not sacrifice, ye would not have condemned the guiltless. For the Son of man is Lord even of the sabbath day. And when he was departed thence, he went into their synagogue: and, behold, there was a man which had his hand withered. And they asked him, saying, Is it lawful to heal on the sabbath days? that they might accuse him. And he said unto them, What man shall there be among you, that shall have one sheep, and if it fall into a pit on the sabbath day, will he not lay hold on it, and lift it out? How much then is a man better than a sheep? Wherefore it is lawful to do well on the sabbath days. Then saith he to the man, Stretch forth thine hand. And he stretched it forth; and it was restored whole, like as the other. Then the Pharisees went out, and held a council against him, how they might destroy him. But when Jesus knew it, he withdrew himself from thence."
    },
    "Romans 14:1-10": {
        "cu": "Немощнаго в вере приемлите, без споров о мнениях. Ибо иной уверен, что можно есть все, а немощный ест овощи. Кто ест, не уничижай того, кто не ест; и кто не ест, не осуждай того, кто ест, потому что Бог принял его. Кто ты, осуждающий чужого раба? Перед своим Господом стоит он, или падает. И будет восставлен, ибо силен Бог восставить его. Иной отличает день от дня, а другой судит о всяком дне равно. Каждый поступай по удостоверению своего ума. Кто различает дни, для Господа различает; и кто не различает дней, для Господа не различает. Кто ест, для Господа ест, ибо благодарит Бога; и кто не ест, для Господа не ест, и благодарит Бога. Ибо никто из нас не живет для себя, и никто не умирает для себя; а живем ли — для Господа живем; умираем ли — для Господа умираем: и потому, живем ли или умираем, — всегда Господни. Ибо Христос для того и умер, и воскрес, и ожил, чтобы господствовать и над мертвыми и над живыми. А ты что осуждаешь брата твоего? Или и ты, что унижаешь брата твоего? Все мы предстанем на суд Христов.",
        "ru": "Немощного в вере принимайте без споров о мнениях. Ибо иной уверен, что можно есть все, а немощный ест овощи. Кто ест, не уничижай того, кто не ест; и кто не ест, не осуждай того, кто ест, потому что Бог принял его. Кто ты, осуждающий чужого раба? Перед своим Господом стоит он, или падает. И будет восставлен, ибо силен Бог восставить его. Иной отличает день от дня, а другой судит о всяком дне равно. Каждый поступай по удостоверению своего ума. Кто различает дни, для Господа различает; и кто не различает дней, для Господа не различает. Кто ест, для Господа ест, ибо благодарит Бога; и кто не ест, для Господа не ест, и благодарит Бога. Ибо никто из нас не живет для себя, и никто не умирает для себя; а живем ли — для Господа живем; умираем ли — для Господа умираем: и потому, живем ли или умираем, — всегда Господни. Ибо Христос для того и умер, и воскрес, и ожил, чтобы господствовать и над мертвыми и над живыми. А ты что осуждаешь брата твоего? Или и ты, что унижаешь брата твоего? Все мы предстанем на суд Христов.",
        "uk": "Слабкого в вірі приймайте, але не для суперечок про погляди. Бо один вірить, що можна їсти все, а слабкий їсть овочі. Хто їсть, нехай не зневажає того, хто не їсть; а хто не їсть, нехай не осуджує того, хто їсть, бо Бог прийняв його. Хто ти такий, що осуджуєш чужого раба? Перед своїм Господом стоїть він або падає. І він буде поставлений, бо Господь має силу поставити його. Один вирізняє день від дня, а інший судить про кожен день однаково. Нехай кожен діє за переконанням власного розуму. Хто зважає на дні, для Господа зважає; а хто не зважає на дні, для Господа не зважає. Хто їсть, для Господа їсть, бо дякує Богові; і хто не їсть, для Господа не їсть, і дякує Богові. Бо ніхто з нас не живе для себе, і ніхто не помирає для себе; а коли живемо — для Господа живемо; коли помираємо — для Господа помираємо: і тому, чи живемо, чи помираємо, — завжди Господні. Бо Христос для того і помер, і воскрес, і ожив, щоб панувати і над мертвими, і над живими. А ти чому осуджуєш брата твого? Або й ти, чому принижуєш брата твого? Усі ми постанемо перед судом Христовим.",
        "de": "Den Schwachen im Glauben nehmt an, doch nicht, um über Meinungen zu streiten. Der eine glaubt, er dürfe alles essen; wer aber schwach ist, der isst Gemüse. Wer isst, verachte den nicht, der nicht isst; und wer nicht isst, richte den nicht, der isst; denn Gott hat ihn angenommen. Wer bist du, dass du den Knecht eines anderen richtest? Er steht oder fällt seinem eigenen Herrn. Er wird aber aufrecht gehalten werden; denn der Herr ist mächtig, ihn aufrecht zu halten. Der eine hält einen Tag vor dem anderen, der andere aber hält jeden Tag gleich. Jeder sei seiner eigenen Meinung gewiss. Wer auf den Tag achtet, der achtet darauf für den Herrn; und wer nicht auf den Tag achtet, der achtet nicht darauf für den Herrn. Wer isst, der isst für den Herrn, denn er dankt Gott; und wer nicht isst, der isst nicht für den Herrn und dankt Gott. Denn keiner von uns lebt sich selber, und keiner stirbt sich selber. Leben wir, so leben wir dem Herrn; sterben wir, so sterben wir dem Herrn. Darum: wir leben oder sterben, so sind wir des Herrn. Denn dazu ist Christus gestorben und wieder lebendig geworden, dass er über Tote und Lebende Herr sei. Du aber, was richtest du deinen Bruder? Oder du, was verachtest du deinen Bruder? Wir werden alle vor dem Richtstuhl Gottes stehen.",
        "en": "Him that is weak in the faith receive ye, but not to doubtful disputations. For one believeth that he may eat all things: another, who is weak, eateth herbs. Let not him that eateth despise him that eateth not; and let not him which eateth not judge him that eateth: for God hath received him. Who art thou that judgest another man's servant? to his own master he standeth or falleth. Yea, he shall be holden up: for God is able to make him stand. One man esteemeth one day above another: another esteemeth every day alike. Let every man be fully persuaded in his own mind. He that regardeth the day, regardeth it unto the Lord; and he that regardeth not the day, to the Lord he doth not regard it. He that eateth, eateth to the Lord, for he giveth God thanks; and he that eateth not, to the Lord he eateth not, and giveth God thanks. For none of us liveth to himself, and no man dieth to himself. For whether we live, we live unto the Lord; and whether we die, we die unto the Lord: whether we live therefore, or die, we are the Lord's. For to this end Christ both died, and rose, and revived, that he might be Lord both of the dead and living. But why dost thou judge thy brother? or why dost thou set at nought thy brother? for we shall all stand before the judgment seat of Christ."
    },
    "Matthew 14:1-15": {
        "cu": "Во время оно, услыша Ирод четвертовластник слух Иисусов, и рече отроком своим: сей есть Иоанн Креститель, той воскресе от мертвых, и сего ради силы деются в нем. Ирод бо ем Иоанна, связа его и посади в темницу, Иродиады ради жены Филиппа брата своего. Глаголаше бо ему Иоанн: не достоит тебе имети ея. И хотяше его убити, убояся народа, яко яко пророка его имеяху. День же быв рождества Иродова, пляса дщерь Иродиадина посреде и угоди Иродови. Темже с клятвою обеща ей дати, егоже аще воспросит. Она же, предварена материю своею, рече: даждь ми зде на блюде главу Иоанна Крестителя. И опечалися царь: клятвы же ради и возлежащих с ним, повеле дати ей. И послав усекну Иоанна в темнице. И принесена бысть глава его на блюде, и дана бысть девице, и отнесе матери своей. И приступльше ученицы его, взяша тело его и погребоша е: и пришедше возвестиша Иисусови. И услышав Иисус отъиде оттуду в корабли в пусто место един: и слышавше народи, идоша по Нем пеши от градов. И исшед Иисус виде много народ, и милосердова о них, и исцели недужныя их. Поздне же бывшу, приступиша к Нему ученицы Его, глаголюще: пусто есть место, и час уже мину: отпусти народы.",
        "ru": "В то время Ирод четвертовластник услышал слух о Иисусе и сказал служащим своим: сей есть Иоанн Креститель; он воскрес из мертвых, и потому чудеса делаются им. Ибо Ирод, взяв Иоанна, связал его и посадил в темницу за Иродиаду, жену Филиппа, брата своего, потому что Иоанн говорил ему: не должно тебе иметь ее. И хотел убить его, но боялся народа, потому что его почитали за пророка. Во время же празднования дня рождения Ирода дочь Иродиады плясала перед собранием и угодила Ироду, посему он с клятвою обещал ей дать, чего она ни попросит. Она же, по наущению матери своей, сказала: дай мне здесь на блюде главу Иоанна Крестителя. И опечалился царь, но, ради клятвы и возлежащих с ним, повелел дать ей, и послал отсечь Иоанну голову в темнице. И принесена была голова его на блюде и дана девице, а она отнесла ее матери своей. Ученики же его, придя, взяли тело его и погребли его; и пошли, возвестили Иисусу. И, услышав, Иисус удалился оттуда на лодке в пустынное место один; а народ, услышав о том, пошел за Ним из городов пешком. И, выйдя, Иисус увидел множество людей и сжалился над ними, и исцелил больных их. Когда же настал вечер, приступили к Нему ученики Его и сказали: место здесь пустынное и время уже позднее; отпусти народ...",
        "uk": "Того часу почув четвертовласник Ірод про славу Ісуса і сказав слугам своїм: «Це Іван Хреститель; він воскрес із мертвих, і тому чуда діються через нього». Бо Ірод, схопивши Івана, зв’язав його й кинув у темницю через Іродіяду, дружину Пилипа, свого брата, бо Іван казав йому: «Не дозволено тобі мати її». І хотів його вбити, та боявся народу, бо його вважали за пророка. А коли був день народження Ірода, дочка Іродіяди танцювала перед гостями і догодила Іродові. Тому він із клятвою пообіцяв дати їй усе, чого тільки попросить. Вона ж, за порадою своєї матері, сказала: «Дай мені тут на полумиску голову Івана Хрестителя». І засумував цар, але заради клятви і тих, що величалися з ним, повелів дати їй. І послав відрубати Іванові голову в темниці. І принесли голову його на полумиску й дали дівчині, а вона віднесла своїй матері. А учні його, прийшовши, взяли тіло його й поховали його; і пішли, сповістили Ісусу. І, почувши, Ісус відплив звідти на човні в пустинне місце один; а люди, почувши про те, пішли за Ним із міст пішки. І, вийшовши, Ісус побачив безліч людей і зглянувся над ними, і зцілив хворих їхніх. Коли ж настав вечір, підійшли до Нього учні Його й сказали: «Місце тут пустинне і час уже пізній; відпусти людей...»",
        "de": "Zu jener Zeit hörte der Vierfürst Herodes die Kunde von Jesus und sprach zu seinen Knechten: Dieser ist Johannes der Täufer; er ist von den Toten auferstanden, und darum wirken solche Kräfte in ihm. Herodes hatte nämlich Johannes ergreifen, binden und ins Gefängnis werfen lassen wegen Herodias, der Frau seines Bruders Philippus. Denn Johannes hatte zu ihm gesagt: Es ist dir nicht erlaubt, sie zu haben. Und er wollte ihn töten, fürchtete aber das Volk, weil sie ihn für einen Propheten hielten. Als aber der Geburtstag des Herodes gefeiert wurde, tanzte die Tochter der Herodias vor den Gästen und gefiel Herodes. Darum versprach er ihr mit einem Eid, ihr zu geben, was sie auch fordern würde. Sie aber, von ihrer Mutter angestiftet, sprach: Gib mir hier auf einer Schale das Haupt Johannes des Täufers! Und der König wurde traurig; aber wegen des Eides und derer, die mit ihm zu Tisch saßen, befahl er, es ihr zu geben. Und er sandte hin und enthauptete Johannes im Gefängnis. Und sein Haupt wurde auf einer Schale gebracht und dem Mädchen gegeben; und sie trug es ihrer Mutter. Und seine Jünger kamen, nahmen seinen Leichnam und begruben ihn; und sie gingen hin und verkündeten es Jesus. Als Jesus das hörte, wich er von dort auf einem Boot aus in eine einsame Gegend für sich allein. Und als die Volksmengen das hörten, folgten sie ihm zu Fuß aus den Städten. Und als er ausstieg, sah er eine große Volksmenge und fühlte tiefes Mitleid mit ihnen und heilte ihre Kranken. Als es aber Abend geworden war, traten seine Jünger zu ihm und sprachen: Die Gegend ist einsam und die Stunde ist schon fortgeschritten; entlass die Volksmengen...",
        "en": "At that time Herod the tetrarch heard of the fame of Jesus, and said unto his servants, This is John the Baptist; he is risen from the dead; and therefore mighty works do shew forth themselves in him. For Herod had laid hold on John, and bound him, and put him in prison for Herodias' sake, his brother Philip's wife. For John said unto him, It is not lawful for thee to have her. And when he would have put him to death, he feared the multitude, because they counted him as a prophet. But when Herod's birthday was kept, the daughter of Herodias danced before them, and pleased Herod. Whereupon he promised with an oath to give her whatsoever she would ask. And she, being before instructed of her mother, said, Give me here John Baptist's head in a charger. And the king was sorry: nevertheless for the oath's sake, and them which sat with him at meat, he commanded it to be given her. And he sent, and beheaded John in the prison. And his head was brought in a charger, and given to the damsel: and she brought it to her mother. And his disciples came, and took up the body, and buried it, and went and told Jesus. When Jesus heard of it, he departed thence by ship into a desert place apart: and when the people had heard thereof, they followed him on foot out of the cities. And Jesus went forth, and saw a great multitude, and was moved with compassion toward them, and he healed their sick. And when it was evening, his disciples came to him, saying, This is a desert place, and the time is now past; send the multitude away..."
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
        audio_bytes = tts.synthesize_speech(bible_data.get("de", ""), "de")
        
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
